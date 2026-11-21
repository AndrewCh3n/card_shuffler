"""Optical corner-index card scanner, USB webcam / Pi Camera capture, and calibration manager."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Protocol, Tuple

from .cards import STANDARD_54, normalize_card

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_TEMPLATES_DIR = DATA_DIR / "templates"
DEFAULT_VISION_CONFIG_PATH = DATA_DIR / "vision_config.json"


class ScanStatus(str, Enum):
    OK = "OK"
    FACE_UP = "FACE_UP"
    UNREADABLE = "UNREADABLE"


@dataclass
class MatchCandidate:
    card: str
    score: float


@dataclass
class ScanResult:
    status: ScanStatus
    card: Optional[str] = None
    confidence: float = 0.0
    message: str = ""
    ink_color: Optional[str] = None  # "red", "black", or None
    top_matches: List[MatchCandidate] = field(default_factory=list)


@dataclass
class VisionConfig:
    """Persisted camera and ROI alignment settings (editable live from the Web UI)."""

    camera_source: str = "webcam"  # "webcam" (USB webcam via OpenCV) | "picamera2" | "mock"
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    roi_x: int = 120
    roi_y: int = 80
    roi_w: int = 180
    roi_h: int = 240
    inner_margin_ratio: float = 0.12  # 12% margin inside ROI gives automatic position-shift tolerance
    min_confidence: float = 0.72
    min_margin: float = 0.04  # Minimum score gap between #1 and #2 candidate
    back_threshold: float = 0.70
    use_color_bonus: bool = True

    def clamped_roi(self, img_w: int, img_h: int) -> Tuple[int, int, int, int]:
        x = max(0, min(self.roi_x, max(0, img_w - 20)))
        y = max(0, min(self.roi_y, max(0, img_h - 20)))
        w = max(20, min(self.roi_w, img_w - x))
        h = max(20, min(self.roi_h, img_h - y))
        return (x, y, w, h)

    def inner_crop_bounds(self, roi_w: int, roi_h: int) -> Tuple[int, int, int, int]:
        """Inner sub-rectangle cropped when saving templates so matchTemplate can slide +-margin."""
        mx = max(2, int(roi_w * self.inner_margin_ratio))
        my = max(2, int(roi_h * self.inner_margin_ratio))
        if roi_w - 2 * mx < 16 or roi_h - 2 * my < 16:
            return (0, 0, roi_w, roi_h)
        return (mx, my, roi_w - 2 * mx, roi_h - 2 * my)


class CardScanner(Protocol):
    def scan_current_card(self) -> ScanResult: ...


class MockCardScanner:
    """Feeds a predetermined sequence of simulated card scans (including optional faults)."""

    def __init__(self, script: Optional[List[ScanResult]] = None) -> None:
        self._script: List[ScanResult] = list(script) if script else []
        self._index: int = 0

    def load_deck(self, cards: List[str], faults: Optional[Dict[int, ScanResult]] = None) -> None:
        faults = faults or {}
        self._script = []
        for idx, card in enumerate(cards):
            if idx in faults:
                self._script.append(faults[idx])
            else:
                self._script.append(ScanResult(status=ScanStatus.OK, card=normalize_card(card), confidence=0.99))
        self._index = 0

    def replace_current_with_valid(self, card: str) -> None:
        if self._index > 0:
            self._script[self._index - 1] = ScanResult(
                status=ScanStatus.OK, card=normalize_card(card), confidence=0.99
            )
            self._index -= 1

    def scan_current_card(self) -> ScanResult:
        if self._index >= len(self._script):
            return ScanResult(
                status=ScanStatus.UNREADABLE,
                confidence=0.0,
                message="No simulated card remaining at scan window.",
            )
        result = self._script[self._index]
        self._index += 1
        return result


def _is_red_card(card_code: str) -> Optional[bool]:
    if card_code in ("JK1", "JK2", "BACK"):
        return None
    return card_code.endswith(("H", "D"))


def _normalize_template_name(code: str) -> str:
    cleaned = code.strip().upper()
    if cleaned == "BACK":
        return "BACK"
    return normalize_card(cleaned)


class OpenCVCornerScanner:
    """Lighting-resilient corner-index recognizer for USB webcams and Pi Camera Module 3.

    How it stays accurate even on a desk webcam:
      1. Captures templates slightly INSIDE the ROI (`inner_margin_ratio = 12%`) so at runtime
         `cv2.matchTemplate` slides automatically across +-12% position jitter.
      2. Normalizes contrast via CLAHE so brightness shifts don't ruin matches.
      3. White-balances the crop against the card's own bright white margin (90th percentile),
         then checks ink redness to distinguish Red suits (H/D) from Black suits (S/C).
    """

    def __init__(
        self,
        templates_dir: Path | str = DEFAULT_TEMPLATES_DIR,
        config: Optional[VisionConfig] = None,
    ) -> None:
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or VisionConfig()

        self._cv2 = None
        self._np = None
        self._clahe = None
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore

            self._cv2 = cv2
            self._np = np
            self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        except ImportError:
            pass

        self._templates: Dict[str, Any] = {}
        self._back_template: Optional[Any] = None
        self._lock = threading.RLock()
        self.reload_templates()

    @property
    def opencv_available(self) -> bool:
        return self._cv2 is not None and self._np is not None

    def reload_templates(self) -> List[str]:
        """Load all saved PNG templates from `templates_dir`."""
        with self._lock:
            self._templates.clear()
            self._back_template = None
            if not self.templates_dir.exists():
                return []

            loaded_names: List[str] = []
            for path in sorted(self.templates_dir.glob("*.png")):
                stem = path.stem.upper()
                try:
                    canonical = _normalize_template_name(stem)
                except ValueError:
                    continue

                if self.opencv_available:
                    img = self._cv2.imread(str(path), self._cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        continue
                else:
                    img = path.read_bytes()

                if canonical == "BACK":
                    self._back_template = img
                else:
                    self._templates[canonical] = img
                loaded_names.append(canonical)
            return loaded_names

    def list_templates(self) -> List[str]:
        with self._lock:
            names = list(self._templates.keys())
            if self._back_template is not None:
                names.insert(0, "BACK")
            return names

    def delete_template(self, code: str) -> bool:
        canonical = _normalize_template_name(code)
        path = self.templates_dir / f"{canonical}.png"
        removed = False
        if path.exists():
            path.unlink()
            removed = True
        with self._lock:
            if canonical == "BACK":
                self._back_template = None
            else:
                self._templates.pop(canonical, None)
        return removed

    def _preprocess_gray(self, bgr_crop: Any) -> Any:
        gray = self._cv2.cvtColor(bgr_crop, self._cv2.COLOR_BGR2GRAY)
        blurred = self._cv2.GaussianBlur(gray, (3, 3), 0)
        return self._clahe.apply(blurred)

    def _estimate_ink_color(self, bgr_crop: Any) -> Optional[str]:
        """Classify corner ink as 'red' or 'black' using self-white-balanced card margin."""
        np = self._np
        arr = bgr_crop.astype(np.float32)
        if arr.size == 0:
            return None

        # 90th-percentile pixel approximates the card's own white background under current lighting
        white_ref = np.percentile(arr.reshape(-1, 3), 90, axis=0)
        white_ref = np.maximum(white_ref, 20.0)
        balanced = np.clip((arr / white_ref) * 255.0, 0, 255)

        luma = 0.114 * balanced[:, :, 0] + 0.587 * balanced[:, :, 1] + 0.299 * balanced[:, :, 2]
        # Ink pixels are significantly darker than the white card background
        ink_mask = luma < 175.0
        if int(np.count_nonzero(ink_mask)) < 40:
            return None

        ink_pixels = balanced[ink_mask]  # BGR order
        b_mean = float(np.mean(ink_pixels[:, 0]))
        g_mean = float(np.mean(ink_pixels[:, 1]))
        r_mean = float(np.mean(ink_pixels[:, 2]))

        # Red ink stays bright in R while dark in B & G; black ink is dark in all 3 channels
        redness = r_mean - 0.5 * (g_mean + b_mean)
        if redness >= 38.0:
            return "red"
        if redness <= 20.0:
            return "black"
        return None

    def save_template_from_frame(self, card_code: str, bgr_frame: Any) -> Path:
        """Crop the inner ROI of `bgr_frame`, preprocess it, and save as `<CARD>.png`."""
        if not self.opencv_available:
            raise RuntimeError("OpenCV is not installed on this machine.")

        canonical = _normalize_template_name(card_code)
        h_img, w_img = bgr_frame.shape[:2]
        rx, ry, rw, rh = self.config.clamped_roi(w_img, h_img)
        roi_bgr = bgr_frame[ry : ry + rh, rx : rx + rw]

        ix, iy, iw, ih = self.config.inner_crop_bounds(rw, rh)
        inner_bgr = roi_bgr[iy : iy + ih, ix : ix + iw]
        processed = self._preprocess_gray(inner_bgr)

        out_path = self.templates_dir / f"{canonical}.png"
        self._cv2.imwrite(str(out_path), processed)

        with self._lock:
            if canonical == "BACK":
                self._back_template = processed
            else:
                self._templates[canonical] = processed
        return out_path

    def _match_score(self, search_gray: Any, tmpl_gray: Any) -> float:
        sh, sw = search_gray.shape[:2]
        th, tw = tmpl_gray.shape[:2]
        # If the user resized the ROI after capturing templates, resize template safely to fit
        if th > sh or tw > sw:
            scale = min((sh - 2) / max(1, th), (sw - 2) / max(1, tw))
            new_w = max(8, int(tw * scale))
            new_h = max(8, int(th * scale))
            tmpl_gray = self._cv2.resize(tmpl_gray, (new_w, new_h), interpolation=self._cv2.INTER_AREA)
        res = self._cv2.matchTemplate(search_gray, tmpl_gray, self._cv2.TM_CCOEFF_NORMED)
        return float(res.max())

    def classify_frame(self, bgr_frame: Any) -> ScanResult:
        """Identify the card corner in `bgr_frame` and return top matches & confidence."""
        if not self.opencv_available:
            return ScanResult(
                status=ScanStatus.UNREADABLE,
                confidence=0.0,
                message="OpenCV is not installed on this machine.",
            )

        h_img, w_img = bgr_frame.shape[:2]
        rx, ry, rw, rh = self.config.clamped_roi(w_img, h_img)
        roi_bgr = bgr_frame[ry : ry + rh, rx : rx + rw]
        search_gray = self._preprocess_gray(roi_bgr)
        ink_color = self._estimate_ink_color(roi_bgr) if self.config.use_color_bonus else None

        with self._lock:
            back_tmpl = self._back_template
            templates_snapshot = dict(self._templates)

        # 1. Check for accidentally face-up card (Bicycle back pattern)
        if back_tmpl is not None:
            back_score = self._match_score(search_gray, back_tmpl)
            if back_score >= self.config.back_threshold:
                return ScanResult(
                    status=ScanStatus.FACE_UP,
                    card=None,
                    confidence=round(back_score, 4),
                    message=f"Card back detected ({back_score:.0%}) — card appears to be face-up.",
                    ink_color=ink_color,
                    top_matches=[MatchCandidate(card="BACK", score=round(back_score, 4))],
                )

        if not templates_snapshot:
            return ScanResult(
                status=ScanStatus.UNREADABLE,
                confidence=0.0,
                message="No card templates calibrated yet! Capture a few test cards first.",
                ink_color=ink_color,
            )

        # 2. Score every calibrated card template (+ gentle Red/Black ink tie-breaker)
        scored: List[MatchCandidate] = []
        for card_code, tmpl_gray in templates_snapshot.items():
            raw_score = self._match_score(search_gray, tmpl_gray)
            adjusted = raw_score
            expected_red = _is_red_card(card_code)
            if ink_color is not None and expected_red is not None:
                if (ink_color == "red" and expected_red) or (ink_color == "black" and not expected_red):
                    adjusted += 0.05
                else:
                    adjusted -= 0.07
            scored.append(MatchCandidate(card=card_code, score=round(min(1.0, max(0.0, adjusted)), 4)))

        scored.sort(key=lambda m: m.score, reverse=True)
        top_matches = scored[:3]
        best = top_matches[0]
        second_score = top_matches[1].score if len(top_matches) > 1 else 0.0
        margin = best.score - second_score

        if best.score >= self.config.min_confidence and (len(top_matches) == 1 or margin >= self.config.min_margin):
            return ScanResult(
                status=ScanStatus.OK,
                card=best.card,
                confidence=best.score,
                message=f"Matched {best.card} ({best.score:.0%})",
                ink_color=ink_color,
                top_matches=top_matches,
            )

        reason = (
            f"Best guess {best.card} ({best.score:.0%}) below threshold ({self.config.min_confidence:.0%})"
            if best.score < self.config.min_confidence
            else f"Ambiguous between {best.card} ({best.score:.0%}) and {top_matches[1].card} ({second_score:.0%})"
        )
        return ScanResult(
            status=ScanStatus.UNREADABLE,
            card=None,
            confidence=best.score,
            message=reason,
            ink_color=ink_color,
            top_matches=top_matches,
        )

    def annotate_frame(self, bgr_frame: Any, last_result: Optional[ScanResult] = None) -> Any:
        """Draw the outer green Search ROI and inner cyan Template Crop Box onto a copy of the frame."""
        vis = bgr_frame.copy()
        h_img, w_img = vis.shape[:2]
        rx, ry, rw, rh = self.config.clamped_roi(w_img, h_img)
        ix, iy, iw, ih = self.config.inner_crop_bounds(rw, rh)

        # Outer green Search ROI
        self._cv2.rectangle(vis, (rx, ry), (rx + rw, ry + rh), (60, 220, 110), 2)
        # Inner cyan Template Capture Zone (place the card's rank+suit index inside this inner box!)
        self._cv2.rectangle(vis, (rx + ix, ry + iy), (rx + ix + iw, ry + iy + ih), (255, 210, 60), 1)
        self._cv2.putText(
            vis,
            "Place corner index inside inner box",
            (rx, max(18, ry - 8)),
            self._cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (255, 220, 80),
            1,
            self._cv2.LINE_AA,
        )

        if last_result is not None:
            if last_result.status == ScanStatus.OK and last_result.card:
                label = f"{last_result.card} ({last_result.confidence:.0%})"
                color = (60, 230, 120)
            elif last_result.status == ScanStatus.FACE_UP:
                label = f"FACE UP ({last_result.confidence:.0%})"
                color = (60, 180, 255)
            else:
                label = f"No match ({last_result.confidence:.0%})"
                color = (90, 90, 255)
            self._cv2.putText(
                vis,
                label,
                (14, h_img - 16),
                self._cv2.FONT_HERSHEY_SIMPLEX,
                0.72,
                color,
                2,
                self._cv2.LINE_AA,
            )
        return vis


class VisionManager:
    """Thread-safe camera & calibration controller backing the Phone/Browser Vision Tab."""

    def __init__(
        self,
        config_path: Path | str = DEFAULT_VISION_CONFIG_PATH,
        templates_dir: Path | str = DEFAULT_TEMPLATES_DIR,
    ) -> None:
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.scanner = OpenCVCornerScanner(templates_dir=templates_dir, config=self.config)

        self._cam_lock = threading.RLock()
        self._cap: Optional[Any] = None
        self._picam2: Optional[Any] = None
        self._last_result: Optional[ScanResult] = None
        self._camera_error: Optional[str] = None

    def _load_config(self) -> VisionConfig:
        if not self.config_path.exists():
            return VisionConfig()
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
            valid_fields = {f for f in VisionConfig.__dataclass_fields__}
            filtered = {k: v for k, v in raw.items() if k in valid_fields}
            return VisionConfig(**filtered)
        except Exception:
            return VisionConfig()

    def _save_config(self) -> None:
        self.config_path.write_text(json.dumps(asdict(self.config), indent=2), encoding="utf-8")

    def update_config(self, updates: Dict[str, Any]) -> VisionConfig:
        reopen_needed = False
        with self._cam_lock:
            for key, val in updates.items():
                if val is None or not hasattr(self.config, key):
                    continue
                if key in ("camera_source", "camera_index", "frame_width", "frame_height"):
                    if getattr(self.config, key) != val:
                        reopen_needed = True
                setattr(self.config, key, val)
            self.scanner.config = self.config
            self._save_config()
            if reopen_needed:
                self.close_camera()
        return self.config

    def status_snapshot(self) -> Dict[str, Any]:
        templates = self.scanner.list_templates()
        return {
            "opencv_available": self.scanner.opencv_available,
            "camera_open": self._cap is not None or self._picam2 is not None,
            "camera_error": self._camera_error,
            "config": asdict(self.config),
            "templates": templates,
            "templates_count": len([t for t in templates if t != "BACK"]),
            "has_back_template": "BACK" in templates,
            "total_possible_cards": len(STANDARD_54),
            "last_result": self._serialize_result(self._last_result) if self._last_result else None,
        }

    @staticmethod
    def _serialize_result(res: ScanResult) -> Dict[str, Any]:
        return {
            "status": res.status.value,
            "card": res.card,
            "confidence": res.confidence,
            "message": res.message,
            "ink_color": res.ink_color,
            "top_matches": [asdict(m) for m in res.top_matches],
        }

    def open_camera(self) -> None:
        with self._cam_lock:
            if not self.scanner.opencv_available:
                self._camera_error = "OpenCV is not installed. Run `bash software/scripts/setup_pi.sh` first."
                raise RuntimeError(self._camera_error)

            if self.config.camera_source == "picamera2":
                if self._picam2 is not None:
                    return
                try:
                    from picamera2 import Picamera2  # type: ignore

                    picam = Picamera2()
                    cfg = picam.create_still_configuration(
                        main={"size": (self.config.frame_width, self.config.frame_height), "format": "RGB888"}
                    )
                    picam.configure(cfg)
                    picam.start()
                    self._picam2 = picam
                    self._camera_error = None
                except Exception as exc:
                    self._camera_error = f"Could not open Pi Camera (picamera2): {exc}"
                    raise RuntimeError(self._camera_error) from exc
                return

            # Default: USB Webcam via OpenCV VideoCapture
            if self._cap is not None and self._cap.isOpened():
                return

            cv2 = self.scanner._cv2
            cap = cv2.VideoCapture(int(self.config.camera_index))
            if not cap.isOpened():
                cap.release()
                self._camera_error = (
                    f"Could not open USB webcam at index {self.config.camera_index}. "
                    "Check USB connection or try camera_index 1 / 2."
                )
                raise RuntimeError(self._camera_error)

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.config.frame_width))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.config.frame_height))
            # Reduce internal frame buffering so snapshots reflect the card currently under the lens
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._cap = cap
            self._camera_error = None

    def close_camera(self) -> None:
        with self._cam_lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
            if self._picam2 is not None:
                try:
                    self._picam2.stop()
                    self._picam2.close()
                except Exception:
                    pass
                self._picam2 = None

    def read_frame(self) -> Any:
        with self._cam_lock:
            self.open_camera()
            if self._picam2 is not None:
                rgb = self._picam2.capture_array()
                return self.scanner._cv2.cvtColor(rgb, self.scanner._cv2.COLOR_RGB2BGR)

            assert self._cap is not None
            # Flush 1 stale buffered frame on USB webcams for snappy live card swaps
            self._cap.grab()
            ok, frame = self._cap.read()
            if not ok or frame is None:
                self._camera_error = "Failed to read frame from USB webcam."
                raise RuntimeError(self._camera_error)
            self._camera_error = None
            return frame

    def capture_template(self, card_code: str) -> Dict[str, Any]:
        frame = self.read_frame()
        saved_path = self.scanner.save_template_from_frame(card_code, frame)
        return {
            "saved": _normalize_template_name(card_code),
            "path": str(saved_path),
            "templates": self.scanner.list_templates(),
        }

    def identify_now(self) -> ScanResult:
        frame = self.read_frame()
        res = self.scanner.classify_frame(frame)
        self._last_result = res
        return res

    def scan_current_card(self) -> ScanResult:
        """CardScanner protocol adapter so ShufflerController can drive VisionManager directly."""
        return self.identify_now()

    def mjpeg_stream(self, fps: float = 10.0) -> Generator[bytes, None, None]:
        """Yield multipart/x-mixed-replace JPEG frames with live ROI overlay for the browser."""
        delay = 1.0 / max(1.0, fps)
        cv2 = self.scanner._cv2
        while True:
            try:
                frame = self.read_frame()
                annotated = self.scanner.annotate_frame(frame, self._last_result)
                ok, jpg = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
                    )
            except Exception:
                break
            time.sleep(delay)
