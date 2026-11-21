"""High-level sort state machine orchestrating ArduinoBridge, CardScanner, and SinglePassSortPlan."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from .cards import MAX_SLOTS, fisher_yates_shuffle
from .planner import SinglePassSortPlan, SortFaultError
from .serial_bridge import ArduinoBridge, ArduinoCommandError, MockArduinoBridge
from .vision import CardScanner, MockCardScanner, ScanResult, ScanStatus


class ShufflerState(str, Enum):
    IDLE = "IDLE"
    HOMING = "HOMING"
    SORTING = "SORTING"
    PAUSED_ALERT = "PAUSED_ALERT"
    UNLOADING = "UNLOADING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


@dataclass
class AlertInfo:
    code: str
    message: str
    card: Optional[str] = None
    missing_cards: List[str] = field(default_factory=list)


class ShufflerController:
    """Thread-safe controller executing single-pass 52/54-card sorts with pause/resume recovery."""

    def __init__(
        self,
        arduino: Optional[ArduinoBridge] = None,
        scanner: Optional[CardScanner] = None,
        simulation: bool = True,
        sim_step_delay_s: float = 0.03,
    ) -> None:
        self.simulation = simulation
        self.arduino: ArduinoBridge = arduino or MockArduinoBridge(step_delay_s=sim_step_delay_s)
        self.scanner: CardScanner = scanner or MockCardScanner()

        self._lock = threading.RLock()
        self._resume_event = threading.Event()
        self._abort_flag = threading.Event()
        self._worker: Optional[threading.Thread] = None

        self.state: ShufflerState = ShufflerState.IDLE
        self.mode_label: str = ""
        self.plan: Optional[SinglePassSortPlan] = None
        self.current_slot: int = MAX_SLOTS - 1
        self.last_card: Optional[str] = None
        self.alert: Optional[AlertInfo] = None
        self.output_deck: List[str] = []
        self.events: List[str] = []

        # Track whether a card is currently sitting in the scan tunnel when paused
        self._card_staged_at_scan: bool = False
        # Simulation-only helper: remember original expected card at a faulted step so "Fix & Resume" works
        self._sim_pending_card_fix: Optional[str] = None
        self._sim_input_deck: List[str] = []
        self._sim_cursor: int = 0

    def _log(self, msg: str) -> None:
        self.events.append(msg)
        if len(self.events) > 80:
            self.events = self.events[-80:]

    def snapshot(self) -> Dict[str, Any]:
        """Return JSON-serializable live status for the Phone Web UI."""
        with self._lock:
            expected = self.plan.expected_count if self.plan else 0
            placed = self.plan.placed_count if self.plan else 0
            slots = dict(self.plan.slot_occupancy) if self.plan else {}
            return {
                "state": self.state.value,
                "simulation": self.simulation,
                "mode_label": self.mode_label,
                "expected_count": expected,
                "placed_count": placed,
                "current_slot": self.current_slot,
                "last_card": self.last_card,
                "slots": slots,
                "alert": (
                    {
                        "code": self.alert.code,
                        "message": self.alert.message,
                        "card": self.alert.card,
                        "missing_cards": list(self.alert.missing_cards),
                    }
                    if self.alert
                    else None
                ),
                "output_deck": list(self.output_deck),
                "events": list(self.events[-20:]),
            }

    def start_sort(
        self,
        target_order: Sequence[str],
        mode_label: str = "Custom Stack",
        sim_input_order: Optional[Sequence[str]] = None,
        sim_fault: Optional[str] = None,
    ) -> None:
        """Start a new single-pass sort in a background thread.

        In simulation mode, `sim_fault` can be one of:
          - `'face_up'`: simulates an accidentally flipped card on card #5
          - `'duplicate'`: simulates a duplicate card on card #8
          - `'missing'`: simulates a hopper running dry 1 card early
          - `'jam'`: simulates an exit-sensor feed jam on card #10
        """
        with self._lock:
            if self.state in (ShufflerState.HOMING, ShufflerState.SORTING, ShufflerState.UNLOADING, ShufflerState.PAUSED_ALERT):
                raise RuntimeError(f"Cannot start new sort while controller is in state {self.state.value}.")

            self.plan = SinglePassSortPlan(target_order=list(target_order))
            self.mode_label = mode_label
            self.alert = None
            self.output_deck = []
            self.last_card = None
            self._card_staged_at_scan = False
            self._sim_pending_card_fix = None
            self.events.clear()
            self._abort_flag.clear()
            self._resume_event.clear()

            if self.simulation:
                self._configure_simulation_deck(
                    expected_count=self.plan.expected_count,
                    sim_input_order=sim_input_order,
                    sim_fault=sim_fault,
                )

            self.state = ShufflerState.HOMING
            self._log(f"Starting sort: {mode_label} ({self.plan.expected_count} cards)")

            self._worker = threading.Thread(target=self._run_sort_loop, name="shuffler-sort", daemon=True)
            self._worker.start()

    def _configure_simulation_deck(
        self,
        expected_count: int,
        sim_input_order: Optional[Sequence[str]],
        sim_fault: Optional[str],
    ) -> None:
        include_jokers = expected_count == 54
        input_deck = list(sim_input_order) if sim_input_order is not None else fisher_yates_shuffle(include_jokers)
        faults: Dict[int, ScanResult] = {}
        jam_index: Optional[int] = None

        if sim_fault == "face_up" and len(input_deck) > 4:
            faults[4] = ScanResult(
                status=ScanStatus.FACE_UP,
                confidence=0.94,
                message="Card #5 appears to be loaded face-up (Bicycle back detected).",
            )
            self._sim_pending_card_fix = input_deck[4]
        elif sim_fault == "duplicate" and len(input_deck) > 7:
            # Replace card #8 with a duplicate of card #1
            self._sim_pending_card_fix = input_deck[7]
            input_deck[7] = input_deck[0]
        elif sim_fault == "missing" and len(input_deck) > 1:
            self._sim_pending_card_fix = input_deck.pop()
        elif sim_fault == "jam" and len(input_deck) > 9:
            jam_index = 9

        self._sim_input_deck = input_deck
        self._sim_cursor = 0

        if isinstance(self.arduino, MockArduinoBridge):
            self.arduino.reset_hopper(count=len(input_deck), inject_jam_on_feed_index=jam_index)
        if isinstance(self.scanner, MockCardScanner):
            self.scanner.load_deck(input_deck, faults=faults)

    def resume(self, fix_simulated_fault: bool = True) -> None:
        """Resume a paused sort after the user fixes a face-up, duplicate, jam, or missing card."""
        with self._lock:
            if self.state != ShufflerState.PAUSED_ALERT:
                raise RuntimeError(f"Cannot resume from state {self.state.value}.")

            alert_code = self.alert.code if self.alert else ""
            if self.simulation and fix_simulated_fault:
                if alert_code in ("FACE_UP_CARD", "UNREADABLE_CARD", "DUPLICATE_CARD") and self._sim_pending_card_fix:
                    if isinstance(self.scanner, MockCardScanner):
                        self.scanner.replace_current_with_valid(self._sim_pending_card_fix)
                    self._log(f"[Sim] User corrected card to {self._sim_pending_card_fix}; resuming scan.")
                    self._sim_pending_card_fix = None
                elif alert_code == "MISSING_CARDS" and self._sim_pending_card_fix:
                    if isinstance(self.arduino, MockArduinoBridge):
                        self.arduino.hopper_cards_remaining += 1
                    if isinstance(self.scanner, MockCardScanner):
                        self.scanner._script.append(
                            ScanResult(status=ScanStatus.OK, card=self._sim_pending_card_fix, confidence=0.99)
                        )
                    self._log(f"[Sim] User inserted missing card {self._sim_pending_card_fix}; resuming.")
                    self._sim_pending_card_fix = None
                elif alert_code == "FEED_JAM":
                    self._log("[Sim] User cleared card jam; resuming eject.")

            self.alert = None
            self.state = ShufflerState.SORTING
            self._resume_event.set()

    def abort(self) -> None:
        """Abort an active or paused sort and return safely to IDLE."""
        with self._lock:
            self._abort_flag.set()
            self._resume_event.set()
            try:
                self.arduino.set_led(0)
                self.arduino.disable_motors()
            except Exception:
                pass
            self.alert = None
            self.state = ShufflerState.IDLE
            self._log("Sort aborted by user.")

    def reset_to_idle(self) -> None:
        with self._lock:
            if self.state in (ShufflerState.COMPLETE, ShufflerState.ERROR, ShufflerState.IDLE):
                self.state = ShufflerState.IDLE
                self.alert = None

    def wait_until_done(self, timeout: float = 30.0) -> ShufflerState:
        """Wait until the sort finishes, pauses, or errors (handy for tests & CLI)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if self.state in (
                    ShufflerState.COMPLETE,
                    ShufflerState.PAUSED_ALERT,
                    ShufflerState.ERROR,
                    ShufflerState.IDLE,
                ):
                    return self.state
            time.sleep(0.01)
        return self.state

    def _pause_for_alert(self, code: str, message: str, card: Optional[str] = None, missing: Optional[List[str]] = None) -> bool:
        """Enter PAUSED_ALERT and block worker until resume() or abort(). Returns False if aborted."""
        with self._lock:
            self.alert = AlertInfo(code=code, message=message, card=card, missing_cards=missing or [])
            self.state = ShufflerState.PAUSED_ALERT
            self._resume_event.clear()
            self._log(f"PAUSED [{code}]: {message}")

        self._resume_event.wait()
        return not self._abort_flag.is_set()

    def _run_sort_loop(self) -> None:
        assert self.plan is not None
        try:
            # 1. Home elevator & close expanding combs
            self.arduino.home()
            with self._lock:
                self.current_slot = MAX_SLOTS - 1
                self.state = ShufflerState.SORTING
                self._log("Elevator homed (slot 53 aligned with feed plane; combs locked closed).")

            self.arduino.set_led(200)

            # 2. Single-pass feed -> scan -> move -> eject loop
            while not self.plan.is_complete:
                if self._abort_flag.is_set():
                    return

                # Stage next card into scan window unless one is already waiting after a pause
                if not self._card_staged_at_scan:
                    try:
                        self.arduino.feed_to_scan()
                        self._card_staged_at_scan = True
                    except ArduinoCommandError as err:
                        if err.code == "HOPPER_EMPTY":
                            missing = self.plan.missing_cards()
                            ok = self._pause_for_alert(
                                code="MISSING_CARDS",
                                message=f"Input hopper empty with {len(missing)} card(s) still missing: {', '.join(missing[:6])}.",
                                missing=missing,
                            )
                            if not ok:
                                return
                            continue
                        else:
                            ok = self._pause_for_alert(
                                code="FEED_TIMEOUT",
                                message=f"Feeder stalled before scan window ({err.detail}). Clear hopper and Resume.",
                            )
                            if not ok:
                                return
                            continue

                # Scan staged card
                scan = self.scanner.scan_current_card()
                if scan.status == ScanStatus.FACE_UP:
                    ok = self._pause_for_alert(
                        code="FACE_UP_CARD",
                        message=scan.message or "Card appears to be face-up. Flip card face-down and Resume.",
                    )
                    if not ok:
                        return
                    continue

                if scan.status == ScanStatus.UNREADABLE or not scan.card:
                    ok = self._pause_for_alert(
                        code="UNREADABLE_CARD",
                        message=scan.message or "Could not identify card index. Check alignment and Resume.",
                    )
                    if not ok:
                        return
                    continue

                # Validate uniqueness & compute target physical elevator slot
                try:
                    assignment = self.plan.assign_scanned_card(scan.card)
                except SortFaultError as fault:
                    ok = self._pause_for_alert(
                        code=fault.code,
                        message=fault.message,
                        card=fault.card,
                    )
                    if not ok:
                        return
                    continue

                # Move elevator to target physical slot
                self.arduino.move_slot(assignment.physical_slot)
                with self._lock:
                    self.current_slot = assignment.physical_slot
                    self.last_card = assignment.card

                # Eject card cleanly into the aligned comb slot (retry loop on jam)
                while True:
                    if self._abort_flag.is_set():
                        return
                    try:
                        self.arduino.eject_to_slot()
                        self._card_staged_at_scan = False
                        break
                    except ArduinoCommandError as err:
                        ok = self._pause_for_alert(
                            code="FEED_JAM",
                            message=f"Exit sensor jam while placing {assignment.card} into slot {assignment.physical_slot} ({err.detail}). Clear card and Resume.",
                            card=assignment.card,
                        )
                        if not ok:
                            return

                with self._lock:
                    self._log(
                        f"Card {self.plan.placed_count}/{self.plan.expected_count}: "
                        f"{assignment.card} -> slot {assignment.physical_slot} (deck pos #{assignment.target_index + 1})"
                    )

            # 3. Unload: return to bottom home (slot 0 just 2 mm above tray) and open expanding combs
            if self._abort_flag.is_set():
                return

            with self._lock:
                self.state = ShufflerState.UNLOADING
                self._log("All cards slotted! Lowering to unload position & opening expanding combs...")

            self.arduino.set_led(0)
            self.arduino.move_slot(MAX_SLOTS - 1)  # ΔZ = 0 mm -> slot 0 is 2 mm above output tray floor!
            with self._lock:
                self.current_slot = MAX_SLOTS - 1

            self.arduino.comb_open()
            self.arduino.comb_close()
            self.arduino.disable_motors()

            result_order = self.plan.simulate_gravity_drop_output()
            with self._lock:
                self.output_deck = result_order
                self.state = ShufflerState.COMPLETE
                self._log(f"Sort complete! {len(result_order)} cards dropped cleanly into output tray.")

        except Exception as exc:
            with self._lock:
                self.state = ShufflerState.ERROR
                self.alert = AlertInfo(code="HARDWARE_ERROR", message=str(exc))
                self._log(f"ERROR: {exc}")
            try:
                self.arduino.set_led(0)
                self.arduino.disable_motors()
            except Exception:
                pass
