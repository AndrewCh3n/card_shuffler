"""Automated tests for cards, stack store, single-pass sort planner, controller recovery, and Web API."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from shuffler.cards import (
    STANDARD_52,
    STANDARD_54,
    fisher_yates_shuffle,
    new_deck_order,
    validate_deck_order,
)
from shuffler.controller import ShufflerController, ShufflerState
from shuffler.planner import SinglePassSortPlan, SortFaultError
from shuffler.serial_bridge import parse_status_line
from shuffler.stacks import StackStore
from shuffler.web_app import create_app


class TestCardsAndPlanner(unittest.TestCase):
    def test_standard_deck_lengths_and_validation(self) -> None:
        self.assertEqual(len(STANDARD_52), 52)
        self.assertEqual(len(STANDARD_54), 54)
        self.assertEqual(len(validate_deck_order(new_deck_order(False))), 52)
        self.assertEqual(len(validate_deck_order(new_deck_order(True))), 54)

        with self.assertRaises(ValueError):
            validate_deck_order(list(STANDARD_52[:-1]))

        dup = list(STANDARD_52)
        dup[-1] = dup[0]
        with self.assertRaises(ValueError):
            validate_deck_order(dup)

    def test_single_pass_slot_mapping_and_gravity_drop(self) -> None:
        target = fisher_yates_shuffle(include_jokers=False)
        plan = SinglePassSortPlan(target_order=target)

        # Top card (index 0) must go to physical slot 51; bottom card (index 51) to slot 0
        self.assertEqual(plan.physical_slot_for(target[0]), 51)
        self.assertEqual(plan.physical_slot_for(target[-1]), 0)

        # Feed an unrelated arbitrary shuffled input deck
        input_deck = fisher_yates_shuffle(include_jokers=False)
        for card in input_deck:
            plan.assign_scanned_card(card)

        self.assertTrue(plan.is_complete)
        self.assertEqual(plan.missing_cards(), [])
        self.assertEqual(plan.simulate_gravity_drop_output(), target)

    def test_54_card_deck_with_jokers(self) -> None:
        target = fisher_yates_shuffle(include_jokers=True)
        plan = SinglePassSortPlan(target_order=target)
        self.assertEqual(plan.physical_slot_for(target[0]), 53)
        self.assertEqual(plan.physical_slot_for(target[-1]), 0)

        for card in reversed(target):
            plan.assign_scanned_card(card)

        self.assertEqual(plan.simulate_gravity_drop_output(), target)

    def test_duplicate_and_unexpected_card_faults(self) -> None:
        plan = SinglePassSortPlan(target_order=new_deck_order(False))
        plan.assign_scanned_card("AS")

        with self.assertRaises(SortFaultError) as ctx_dup:
            plan.assign_scanned_card("AS")
        self.assertEqual(ctx_dup.exception.code, "DUPLICATE_CARD")

        with self.assertRaises(SortFaultError) as ctx_unexp:
            plan.assign_scanned_card("JK1")
        self.assertEqual(ctx_unexp.exception.code, "UNEXPECTED_CARD")


class TestSerialParserAndStackStore(unittest.TestCase):
    def test_parse_status_line(self) -> None:
        st = parse_status_line("OK SLOT=12 HOMED=1 HOPPER=1 SCAN=0 EXIT=1 COMB=OPEN")
        self.assertEqual(st.slot, 12)
        self.assertTrue(st.homed)
        self.assertTrue(st.hopper_has_cards)
        self.assertFalse(st.card_at_scan)
        self.assertTrue(st.card_at_exit)
        self.assertTrue(st.comb_open)

    def test_custom_stack_crud(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store_file = Path(tmp) / "stacks.json"
            store = StackStore(store_file)

            # Built-in NDO present by default
            self.assertIsNotNone(store.get_stack("new-deck-order"))

            custom_order = fisher_yates_shuffle(include_jokers=False)
            saved = store.save_stack("My Trick Stack", custom_order)
            self.assertEqual(saved.id, "my-trick-stack")
            self.assertEqual(saved.cards, custom_order)

            # Reload from disk to verify persistence
            reloaded = StackStore(store_file)
            fetched = reloaded.get_stack("my-trick-stack")
            self.assertIsNotNone(fetched)
            assert fetched is not None
            self.assertEqual(fetched.cards, custom_order)

            # Cannot delete built-in stack
            with self.assertRaises(ValueError):
                reloaded.delete_stack("new-deck-order")

            self.assertTrue(reloaded.delete_stack("my-trick-stack"))
            self.assertIsNone(reloaded.get_stack("my-trick-stack"))


class TestControllerFaultRecovery(unittest.TestCase):
    def _run_with_fault(self, fault_name: str, expected_code: str) -> None:
        ctrl = ShufflerController(simulation=True, sim_step_delay_s=0.0)
        target = fisher_yates_shuffle(include_jokers=False)
        ctrl.start_sort(target_order=target, mode_label=f"Test {fault_name}", sim_fault=fault_name)

        state = ctrl.wait_until_done(timeout=5.0)
        self.assertEqual(state, ShufflerState.PAUSED_ALERT)
        snap = ctrl.snapshot()
        self.assertIsNotNone(snap["alert"])
        self.assertEqual(snap["alert"]["code"], expected_code)

        ctrl.resume(fix_simulated_fault=True)
        final_state = ctrl.wait_until_done(timeout=5.0)
        self.assertEqual(final_state, ShufflerState.COMPLETE)
        self.assertEqual(ctrl.snapshot()["output_deck"], target)

    def test_clean_sort(self) -> None:
        ctrl = ShufflerController(simulation=True, sim_step_delay_s=0.0)
        target = fisher_yates_shuffle(include_jokers=True)
        ctrl.start_sort(target_order=target, mode_label="Clean 54")
        self.assertEqual(ctrl.wait_until_done(timeout=5.0), ShufflerState.COMPLETE)
        self.assertEqual(ctrl.snapshot()["output_deck"], target)

    def test_face_up_pause_and_resume(self) -> None:
        self._run_with_fault("face_up", "FACE_UP_CARD")

    def test_duplicate_pause_and_resume(self) -> None:
        self._run_with_fault("duplicate", "DUPLICATE_CARD")

    def test_missing_card_pause_and_resume(self) -> None:
        self._run_with_fault("missing", "MISSING_CARDS")

    def test_jam_pause_and_resume(self) -> None:
        self._run_with_fault("jam", "FEED_JAM")


class TestWebAPI(unittest.TestCase):
    def test_web_endpoints_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctrl = ShufflerController(simulation=True, sim_step_delay_s=0.0)
            app = create_app(
                store_path=Path(tmp) / "stacks.json",
                controller=ctrl,
                vision_config_path=Path(tmp) / "vision_config.json",
                templates_dir=Path(tmp) / "templates",
            )

            config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error")
            server = uvicorn.Server(config)
            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()

            while not server.started:
                pass

            # Discover dynamically bound port
            port = server.servers[0].sockets[0].getsockname()[1]
            base = f"http://127.0.0.1:{port}"

            try:
                # 1. Serve phone UI HTML
                with urllib.request.urlopen(f"{base}/") as resp:
                    html = resp.read().decode("utf-8")
                    self.assertIn("Custom Stack Builder", html)

                # 2. Save a custom stack
                order = fisher_yates_shuffle(False)
                req = urllib.request.Request(
                    f"{base}/api/stacks",
                    data=json.dumps({"name": "Stage Routine", "cards": order}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(body["stack"]["id"], "stage-routine")

                # 3. Trigger sort into that saved stack
                req_sort = urllib.request.Request(
                    f"{base}/api/sort/stack/stage-routine",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req_sort) as resp:
                    self.assertEqual(resp.status, 200)

                self.assertEqual(ctrl.wait_until_done(timeout=5.0), ShufflerState.COMPLETE)

                with urllib.request.urlopen(f"{base}/api/status") as resp:
                    status = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(status["state"], "COMPLETE")
                    self.assertEqual(status["output_deck"], order)

                # 4. Vision status & ROI config update API
                with urllib.request.urlopen(f"{base}/api/vision/status") as resp:
                    vstat = json.loads(resp.read().decode("utf-8"))
                    self.assertIn("config", vstat)
                    self.assertEqual(vstat["config"]["camera_source"], "webcam")

                req_vcfg = urllib.request.Request(
                    f"{base}/api/vision/config",
                    data=json.dumps({"roi_x": 95, "roi_y": 55, "roi_w": 160, "roi_h": 210}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req_vcfg) as resp:
                    vcfg_body = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(vcfg_body["config"]["roi_x"], 95)
                    self.assertEqual(vcfg_body["config"]["roi_h"], 210)
            finally:
                server.should_exit = True
                thread.join(timeout=3.0)


class TestVisionConfigAndTemplates(unittest.TestCase):
    def test_vision_config_and_template_inventory(self) -> None:
        from shuffler.vision import VisionConfig, VisionManager

        cfg = VisionConfig(roi_x=100, roi_y=50, roi_w=180, roi_h=240)
        self.assertEqual(cfg.clamped_roi(640, 480), (100, 50, 180, 240))
        self.assertEqual(cfg.clamped_roi(150, 100), (100, 50, 50, 50))
        ix, iy, iw, ih = cfg.inner_crop_bounds(180, 240)
        self.assertGreater(ix, 0)
        self.assertGreater(iy, 0)
        self.assertLess(iw, 180)
        self.assertLess(ih, 240)

        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "vision_config.json"
            tmpl_dir = Path(tmp) / "templates"
            tmpl_dir.mkdir()
            # Drop placeholder template files to verify inventory & deletion
            (tmpl_dir / "BACK.png").write_bytes(b"fake-png-back")
            (tmpl_dir / "AS.png").write_bytes(b"fake-png-as")
            (tmpl_dir / "10H.png").write_bytes(b"fake-png-10h")

            vm = VisionManager(config_path=cfg_path, templates_dir=tmpl_dir)
            vm.update_config({"roi_x": 77, "camera_index": 1})

            # Reload from disk to confirm persistence
            vm2 = VisionManager(config_path=cfg_path, templates_dir=tmpl_dir)
            self.assertEqual(vm2.config.roi_x, 77)
            self.assertEqual(vm2.config.camera_index, 1)

            snap = vm2.status_snapshot()
            self.assertTrue(snap["has_back_template"])
            self.assertEqual(snap["templates_count"], 2)
            self.assertIn("AS", snap["templates"])
            self.assertIn("10H", snap["templates"])

            self.assertTrue(vm2.scanner.delete_template("AS"))
            self.assertNotIn("AS", vm2.scanner.list_templates())


if __name__ == "__main__":
    unittest.main()
