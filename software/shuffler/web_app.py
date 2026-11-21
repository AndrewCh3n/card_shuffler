"""FastAPI Phone/Browser Wi-Fi Web UI and REST API for the Programmable Card Shuffler."""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from .cards import fisher_yates_shuffle
from .controller import ShufflerController
from .serial_bridge import SerialArduinoBridge
from .stacks import DEFAULT_STORE_PATH, StackStore
from .vision import DEFAULT_TEMPLATES_DIR, DEFAULT_VISION_CONFIG_PATH, VisionManager

STATIC_DIR = Path(__file__).resolve().parent / "static"


class SaveStackRequest(BaseModel):
    name: str
    cards: List[str]
    stack_id: Optional[str] = None


class StartRandomRequest(BaseModel):
    include_jokers: bool = False
    sim_fault: Optional[str] = None


class StartStackRequest(BaseModel):
    sim_fault: Optional[str] = None


class VisionConfigUpdate(BaseModel):
    camera_source: Optional[str] = None
    camera_index: Optional[int] = None
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    roi_x: Optional[int] = None
    roi_y: Optional[int] = None
    roi_w: Optional[int] = None
    roi_h: Optional[int] = None
    min_confidence: Optional[float] = None
    min_margin: Optional[float] = None
    back_threshold: Optional[float] = None
    use_color_bonus: Optional[bool] = None


class CaptureTemplateRequest(BaseModel):
    card: str


def create_app(
    store_path: Path | str = DEFAULT_STORE_PATH,
    controller: Optional[ShufflerController] = None,
    vision: Optional[VisionManager] = None,
    vision_config_path: Path | str = DEFAULT_VISION_CONFIG_PATH,
    templates_dir: Path | str = DEFAULT_TEMPLATES_DIR,
) -> FastAPI:
    app = FastAPI(title="Card Shuffler Phone UI", version="0.2.0")
    store = StackStore(path=store_path)

    if vision is None:
        vision = VisionManager(config_path=vision_config_path, templates_dir=templates_dir)

    if controller is None:
        sim_mode = os.environ.get("SHUFFLER_SIM", "1") != "0"
        if sim_mode:
            delay = float(os.environ.get("SHUFFLER_SIM_DELAY", "0.04"))
            controller = ShufflerController(simulation=True, sim_step_delay_s=delay)
        else:
            port = os.environ.get("SHUFFLER_ARDUINO_PORT", "/dev/ttyUSB0")
            arduino = SerialArduinoBridge(port=port)
            controller = ShufflerController(arduino=arduino, scanner=vision, simulation=False)

    app.state.store = store
    app.state.controller = controller
    app.state.vision = vision

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    # ------------------------------------------------------------------------
    # Sort & Custom Stacks API
    # ------------------------------------------------------------------------
    @app.get("/api/status")
    def get_status():
        return controller.snapshot()

    @app.get("/api/stacks")
    def list_stacks():
        return {"stacks": [asdict(s) for s in store.list_stacks()]}

    @app.post("/api/stacks")
    def save_stack(req: SaveStackRequest):
        try:
            saved = store.save_stack(name=req.name, cards=req.cards, stack_id=req.stack_id)
            return {"stack": asdict(saved)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/stacks/{stack_id}")
    def delete_stack(stack_id: str):
        try:
            deleted = store.delete_stack(stack_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Stack {stack_id!r} not found.")
        return {"deleted": stack_id}

    @app.post("/api/sort/random")
    def start_random_sort(req: StartRandomRequest):
        target = fisher_yates_shuffle(include_jokers=req.include_jokers)
        label = f"Random Shuffle ({54 if req.include_jokers else 52})"
        try:
            controller.start_sort(target_order=target, mode_label=label, sim_fault=req.sim_fault)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return controller.snapshot()

    @app.post("/api/sort/stack/{stack_id}")
    def start_stack_sort(stack_id: str, req: Optional[StartStackRequest] = None):
        stack = store.get_stack(stack_id)
        if not stack:
            raise HTTPException(status_code=404, detail=f"Stack {stack_id!r} not found.")
        sim_fault = req.sim_fault if req else None
        try:
            controller.start_sort(target_order=stack.cards, mode_label=stack.name, sim_fault=sim_fault)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return controller.snapshot()

    @app.post("/api/sort/resume")
    def resume_sort():
        try:
            controller.resume(fix_simulated_fault=True)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return controller.snapshot()

    @app.post("/api/sort/abort")
    def abort_sort():
        controller.abort()
        return controller.snapshot()

    @app.post("/api/sort/reset")
    def reset_sort():
        controller.reset_to_idle()
        return controller.snapshot()

    # ------------------------------------------------------------------------
    # Live Vision, Webcam Calibration & Card Identification API
    # ------------------------------------------------------------------------
    @app.get("/api/vision/status")
    def get_vision_status():
        return vision.status_snapshot()

    @app.post("/api/vision/config")
    def update_vision_config(req: VisionConfigUpdate):
        updates = req.model_dump(exclude_none=True)
        cfg = vision.update_config(updates)
        return {"config": asdict(cfg), "status": vision.status_snapshot()}

    @app.get("/api/vision/stream")
    def vision_stream():
        try:
            vision.open_camera()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return StreamingResponse(
            vision.mjpeg_stream(fps=10.0),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    @app.post("/api/vision/close")
    def close_vision_camera():
        vision.close_camera()
        return vision.status_snapshot()

    @app.post("/api/vision/capture")
    def capture_card_template(req: CaptureTemplateRequest):
        try:
            res = vision.capture_template(req.card)
            return res
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.delete("/api/vision/templates/{card}")
    def delete_card_template(card: str):
        try:
            deleted = vision.scanner.delete_template(card)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Template {card!r} not found.")
        return {"deleted": card.upper(), "templates": vision.scanner.list_templates()}

    @app.post("/api/vision/identify")
    def identify_card_now():
        try:
            res = vision.identify_now()
            return vision._serialize_result(res)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return app


app = create_app()
