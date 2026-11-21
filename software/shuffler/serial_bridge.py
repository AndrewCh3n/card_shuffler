"""Pi <-> Arduino USB Serial protocol bridge and hardware-free MockArduinoBridge."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol

from .cards import MAX_SLOTS


class ArduinoCommandError(Exception):
    """Raised when the Arduino returns an ERR response or times out."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass
class HardwareStatus:
    slot: int
    homed: bool
    hopper_has_cards: bool
    card_at_scan: bool
    card_at_exit: bool
    comb_open: bool


class ArduinoBridge(Protocol):
    """Minimal protocol implemented by both real serial hardware and the simulator."""

    def ping(self) -> None: ...
    def status(self) -> HardwareStatus: ...
    def home(self) -> None: ...
    def move_slot(self, slot: int) -> None: ...
    def feed_to_scan(self) -> None: ...
    def eject_to_slot(self) -> None: ...
    def nudge_feed(self, steps: int) -> None: ...
    def comb_open(self) -> None: ...
    def comb_close(self) -> None: ...
    def set_led(self, brightness: int) -> None: ...
    def disable_motors(self) -> None: ...
    def estop(self) -> None: ...


def parse_status_line(reply: str) -> HardwareStatus:
    """Parse Arduino STATUS reply: `OK SLOT=53 HOMED=1 HOPPER=1 SCAN=0 EXIT=0 COMB=CLOSED`."""
    tokens = reply.strip().split()
    if not tokens or tokens[0] != "OK":
        raise ArduinoCommandError("BAD_REPLY", reply)

    kv: Dict[str, str] = {}
    for tok in tokens[1:]:
        if "=" in tok:
            k, v = tok.split("=", 1)
            kv[k] = v

    return HardwareStatus(
        slot=int(kv.get("SLOT", MAX_SLOTS - 1)),
        homed=kv.get("HOMED", "0") == "1",
        hopper_has_cards=kv.get("HOPPER", "0") == "1",
        card_at_scan=kv.get("SCAN", "0") == "1",
        card_at_exit=kv.get("EXIT", "0") == "1",
        comb_open=kv.get("COMB", "CLOSED").upper() == "OPEN",
    )


class SerialArduinoBridge:
    """Real USB Serial bridge to Arduino Nano/Uno running shuffler_controller.ino."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200, timeout: float = 15.0) -> None:
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "pyserial is not installed. Run `pip install pyserial` on the Raspberry Pi/PC."
            ) from exc

        self._ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        # Arduino Nano/Uno resets when USB serial opens; wait briefly for boot banner
        time.sleep(2.0)
        self._ser.reset_input_buffer()

    def close(self) -> None:
        self._ser.close()

    def _send(self, cmd: str) -> str:
        payload = f"{cmd.strip()}\n".encode("ascii")
        self._ser.write(payload)
        self._ser.flush()
        raw = self._ser.readline().decode("ascii", errors="replace").strip()
        if not raw:
            raise ArduinoCommandError("TIMEOUT", f"No response for command: {cmd}")
        if raw.startswith("ERR"):
            parts = raw.split(" ", 2)
            code = parts[1] if len(parts) > 1 else "UNKNOWN"
            detail = parts[2] if len(parts) > 2 else ""
            raise ArduinoCommandError(code, detail)
        if not raw.startswith("OK"):
            raise ArduinoCommandError("BAD_REPLY", raw)
        return raw

    def ping(self) -> None:
        self._send("PING")

    def status(self) -> HardwareStatus:
        return parse_status_line(self._send("STATUS"))

    def home(self) -> None:
        self._send("HOME")

    def move_slot(self, slot: int) -> None:
        self._send(f"MOVE_SLOT {slot}")

    def feed_to_scan(self) -> None:
        self._send("FEED_TO_SCAN")

    def eject_to_slot(self) -> None:
        self._send("EJECT_TO_SLOT")

    def nudge_feed(self, steps: int) -> None:
        self._send(f"NUDGE_FEED {steps}")

    def comb_open(self) -> None:
        self._send("COMB_OPEN")

    def comb_close(self) -> None:
        self._send("COMB_CLOSE")

    def set_led(self, brightness: int) -> None:
        self._send(f"LED {max(0, min(255, int(brightness)))}")

    def disable_motors(self) -> None:
        self._send("DISABLE_MOTORS")

    def estop(self) -> None:
        self._send("ESTOP")


@dataclass
class MockArduinoBridge:
    """In-memory mechanical simulator for testing full sorts without physical hardware."""

    step_delay_s: float = 0.0
    hopper_cards_remaining: int = 52
    inject_jam_on_feed_index: Optional[int] = None

    homed: bool = False
    current_slot: int = MAX_SLOTS - 1
    comb_is_open: bool = False
    led_brightness: int = 0
    card_at_scan: bool = False
    feeds_completed: int = 0
    command_log: List[str] = field(default_factory=list)
    _jam_already_triggered: bool = False

    def _sleep(self, factor: float = 1.0) -> None:
        if self.step_delay_s > 0:
            time.sleep(self.step_delay_s * factor)

    def reset_hopper(self, count: int, inject_jam_on_feed_index: Optional[int] = None) -> None:
        self.hopper_cards_remaining = count
        self.card_at_scan = False
        self.feeds_completed = 0
        self.inject_jam_on_feed_index = inject_jam_on_feed_index
        self._jam_already_triggered = False

    def ping(self) -> None:
        self.command_log.append("PING")

    def status(self) -> HardwareStatus:
        self.command_log.append("STATUS")
        return HardwareStatus(
            slot=self.current_slot,
            homed=self.homed,
            hopper_has_cards=self.hopper_cards_remaining > 0,
            card_at_scan=self.card_at_scan,
            card_at_exit=False,
            comb_open=self.comb_is_open,
        )

    def home(self) -> None:
        self.command_log.append("HOME")
        self._sleep(2.0)
        self.comb_is_open = False
        self.current_slot = MAX_SLOTS - 1
        self.homed = True

    def move_slot(self, slot: int) -> None:
        self.command_log.append(f"MOVE_SLOT {slot}")
        if not self.homed:
            raise ArduinoCommandError("NOT_HOMED", "Run HOME before MOVE_SLOT")
        if not (0 <= slot < MAX_SLOTS):
            raise ArduinoCommandError("BAD_SLOT", f"Slot {slot} out of range 0..{MAX_SLOTS - 1}")
        self.comb_is_open = False
        hop_distance = abs(slot - self.current_slot)
        self._sleep(0.2 + hop_distance * 0.02)
        self.current_slot = slot

    def feed_to_scan(self) -> None:
        self.command_log.append("FEED_TO_SCAN")
        if self.hopper_cards_remaining <= 0:
            raise ArduinoCommandError("HOPPER_EMPTY", "No cards detected in input hopper")
        self._sleep(0.5)
        self.hopper_cards_remaining -= 1
        self.card_at_scan = True

    def eject_to_slot(self) -> None:
        self.command_log.append("EJECT_TO_SLOT")
        if (
            self.inject_jam_on_feed_index is not None
            and self.feeds_completed == self.inject_jam_on_feed_index
            and not self._jam_already_triggered
        ):
            self._jam_already_triggered = True
            raise ArduinoCommandError("JAM_DETECTED", "Simulated card jam at slot exit sensor")
        self._sleep(0.5)
        self.card_at_scan = False
        self.feeds_completed += 1

    def nudge_feed(self, steps: int) -> None:
        self.command_log.append(f"NUDGE_FEED {steps}")
        self._sleep(0.2)

    def comb_open(self) -> None:
        self.command_log.append("COMB_OPEN")
        self._sleep(1.5)
        self.comb_is_open = True

    def comb_close(self) -> None:
        self.command_log.append("COMB_CLOSE")
        self._sleep(0.8)
        self.comb_is_open = False

    def set_led(self, brightness: int) -> None:
        self.command_log.append(f"LED {brightness}")
        self.led_brightness = max(0, min(255, int(brightness)))

    def disable_motors(self) -> None:
        self.command_log.append("DISABLE_MOTORS")

    def estop(self) -> None:
        self.command_log.append("ESTOP")
        self.homed = False
