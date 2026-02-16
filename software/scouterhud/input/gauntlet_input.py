"""ScouterGauntlet BLE input backend.

Connects to a ScouterGauntlet via BLE and receives touch events
through a custom GATT service. Translates pad events into InputEvents
that the app state machine consumes.

Requires: bleak (BLE client library)
Hardware: ESP32-S3 running ScouterGauntlet firmware

BLE GATT Service (custom):
  Service UUID:        a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f01
  Input Event (notify): a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f02
  Mode Status (r/w):    a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f03
  Haptic Command (w):   a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f04
  Battery Level (r/n):  a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f05
"""

import asyncio
import json
import logging
import struct
import threading
from collections import deque
from enum import IntEnum

from scouterhud.input.backend import InputBackend
from scouterhud.input.events import EventType, InputEvent

log = logging.getLogger("scouterhud.input.gauntlet")

try:
    from bleak import BleakClient, BleakScanner
    _HAS_BLEAK = True
except ImportError:
    _HAS_BLEAK = False

# ── BLE UUIDs ──

SERVICE_UUID = "a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f01"
CHAR_INPUT_EVENT = "a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f02"
CHAR_MODE_STATUS = "a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f03"
CHAR_HAPTIC_CMD = "a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f04"
CHAR_BATTERY = "a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f05"

# Device advertised name prefix
GAUNTLET_NAME_PREFIX = "ScouterGauntlet"


class PadEvent(IntEnum):
    """Touch event types from the Gauntlet firmware.

    Wire format: 1 byte event_type + 1 byte pad_mask + 2 bytes timestamp_ms
    """
    TAP = 0x01
    RELEASE = 0x02
    HOLD = 0x03
    DOUBLE_TAP = 0x04
    CHORD = 0x10


class HapticPattern(IntEnum):
    """Haptic feedback patterns sent to the Gauntlet."""
    SHORT = 0x01       # 50ms — input acknowledged
    DOUBLE = 0x02      # 2× 50ms — mode changed
    LONG = 0x03        # 200ms — error
    SUCCESS = 0x04     # 3× short ascending — auth OK


# ── Pad-to-event mapping ──

# Mode 1: Navigation — single pad taps
_NAV_MAP = {
    0b00001: EventType.NAV_LEFT,      # PAD 1
    0b00010: EventType.NAV_UP,        # PAD 2
    0b00100: EventType.NAV_DOWN,      # PAD 3
    0b01000: EventType.NAV_RIGHT,     # PAD 4
    0b10000: EventType.CONFIRM,       # PAD 5
}

# Mode 1: Navigation — chord gestures
_NAV_CHORD_MAP = {
    0b01001: EventType.CANCEL,        # PAD 1+4 hold
}

# Mode 1: Navigation — double-tap
_NAV_DOUBLE_TAP_MAP = {
    0b10000: EventType.HOME,          # PAD 5 double-tap
}

# Mode 2: Numeric — single pad taps (PIN entry)
_NUMERIC_MAP = {
    0b00001: EventType.DIGIT_DOWN,    # PAD 1 — decrement
    0b00010: EventType.DIGIT_PREV,    # PAD 2 — prev digit
    0b00100: EventType.DIGIT_NEXT,    # PAD 3 — next digit
    0b01000: EventType.DIGIT_UP,      # PAD 4 — increment
    0b10000: EventType.DIGIT_SUBMIT,  # PAD 5 — confirm
}

# Quick actions (any mode)
_GESTURE_MAP = {
    # Swipe 1→4 = next device (detected as sequential chord)
    "swipe_right": EventType.NEXT_DEVICE,
    # Swipe 4→1 = prev device
    "swipe_left": EventType.PREV_DEVICE,
    # Hold all pads 3s = lock
    "hold_all": EventType.LOCK,
    # Triple-tap PAD 5 = scan QR
    "triple_5": EventType.SCAN_QR,
    # Hold PAD 5 2s = toggle voice
    "hold_5": EventType.TOGGLE_VOICE,
}


class GauntletInput(InputBackend):
    """BLE client for the ScouterGauntlet.

    Runs a background asyncio loop that:
    1. Scans for a nearby Gauntlet via BLE advertisement
    2. Connects and subscribes to input_event notifications
    3. Translates pad events into InputEvents
    4. Queues them for the main thread to poll()
    """

    def __init__(self, device_address: str | None = None):
        """Initialize the Gauntlet BLE backend.

        Args:
            device_address: Optional BLE MAC address. If None, will scan
                            for any device advertising as "ScouterGauntlet*".
        """
        self._target_address = device_address
        self._queue: deque[InputEvent] = deque(maxlen=64)
        self._numeric_mode = False
        self._connected = False
        self._running = False
        self._battery_pct: int | None = None

        # Background thread for asyncio BLE loop
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client: "BleakClient | None" = None

    @property
    def name(self) -> str:
        return "gauntlet-ble"

    @property
    def numeric_mode(self) -> bool:
        return self._numeric_mode

    @numeric_mode.setter
    def numeric_mode(self, value: bool) -> None:
        self._numeric_mode = value
        # Notify the Gauntlet of mode change (async, fire-and-forget)
        if self._connected and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._send_mode_update(), self._loop
            )

    @property
    def is_available(self) -> bool:
        return _HAS_BLEAK and self._connected

    @property
    def battery_level(self) -> int | None:
        """Last known battery percentage, or None if unknown."""
        return self._battery_pct

    def start(self) -> None:
        if not _HAS_BLEAK:
            log.warning(
                "bleak not installed — Gauntlet BLE disabled. "
                "Install with: pip install bleak"
            )
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_ble_loop,
            name="gauntlet-ble",
            daemon=True,
        )
        self._thread.start()
        log.info("Gauntlet BLE backend started (scanning...)")

    def stop(self) -> None:
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=5.0)
        self._connected = False
        log.info("Gauntlet BLE backend stopped")

    def poll(self) -> InputEvent | None:
        if self._queue:
            return self._queue.popleft()
        return None

    def send_haptic(self, pattern: HapticPattern) -> None:
        """Send a haptic feedback command to the Gauntlet."""
        if self._connected and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._write_haptic(pattern), self._loop
            )

    # ── Background BLE loop ──

    def _run_ble_loop(self) -> None:
        """Entry point for the background BLE thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._ble_main())
        except Exception as e:
            log.error(f"BLE loop error: {e}")
        finally:
            self._loop.close()

    async def _ble_main(self) -> None:
        """Main BLE coroutine: scan, connect, reconnect loop."""
        while self._running:
            address = self._target_address or await self._scan_for_gauntlet()
            if not address:
                await asyncio.sleep(3.0)
                continue

            try:
                await self._connect_and_listen(address)
            except Exception as e:
                log.warning(f"BLE connection lost: {e}")
                self._connected = False

            if self._running:
                log.info("Reconnecting in 2s...")
                await asyncio.sleep(2.0)

    async def _scan_for_gauntlet(self) -> str | None:
        """Scan for a ScouterGauntlet BLE device. Returns address or None."""
        log.debug("Scanning for ScouterGauntlet...")
        try:
            devices = await BleakScanner.discover(timeout=5.0)
            for d in devices:
                if d.name and d.name.startswith(GAUNTLET_NAME_PREFIX):
                    log.info(f"Found Gauntlet: {d.name} ({d.address})")
                    return d.address
        except Exception as e:
            log.debug(f"BLE scan error: {e}")
        return None

    async def _connect_and_listen(self, address: str) -> None:
        """Connect to the Gauntlet and subscribe to notifications."""
        async with BleakClient(address) as client:
            self._client = client
            self._connected = True
            log.info(f"Connected to Gauntlet at {address}")

            # Subscribe to input events
            await client.start_notify(
                CHAR_INPUT_EVENT, self._on_input_notification
            )

            # Subscribe to battery level
            try:
                await client.start_notify(
                    CHAR_BATTERY, self._on_battery_notification
                )
            except Exception:
                log.debug("Battery characteristic not available")

            # Send initial mode
            await self._send_mode_update()

            # Keep alive while connected
            while self._running and client.is_connected:
                await asyncio.sleep(0.5)

            self._connected = False
            self._client = None

    # ── Notification handlers ──

    def _on_input_notification(self, _sender, data: bytearray) -> None:
        """Handle input_event BLE notification from the Gauntlet.

        Wire format (4 bytes):
            [0] event_type (PadEvent)
            [1] pad_mask (bitmask of pads 1-5)
            [2:4] timestamp_ms (uint16 little-endian, wrapping)
        """
        if len(data) < 4:
            return

        event_type = data[0]
        pad_mask = data[1]
        # timestamp_ms = struct.unpack_from("<H", data, 2)[0]  # available if needed

        mapped = self._translate_event(event_type, pad_mask)
        if mapped:
            self._queue.append(mapped)

    def _on_battery_notification(self, _sender, data: bytearray) -> None:
        """Handle battery level notification."""
        if len(data) >= 1:
            self._battery_pct = data[0]

    # ── Event translation ──

    def _translate_event(self, event_type: int, pad_mask: int) -> InputEvent | None:
        """Translate a raw Gauntlet pad event into an InputEvent."""
        if event_type == PadEvent.TAP:
            if self._numeric_mode:
                etype = _NUMERIC_MAP.get(pad_mask)
            else:
                etype = _NAV_MAP.get(pad_mask)
            if etype:
                return InputEvent(type=etype, source="gauntlet")

        elif event_type == PadEvent.CHORD:
            etype = _NAV_CHORD_MAP.get(pad_mask)
            if etype:
                return InputEvent(type=etype, source="gauntlet")

        elif event_type == PadEvent.DOUBLE_TAP:
            etype = _NAV_DOUBLE_TAP_MAP.get(pad_mask)
            if etype:
                return InputEvent(type=etype, source="gauntlet")

        elif event_type == PadEvent.HOLD:
            # Hold PAD 5 (2s) = toggle voice
            if pad_mask == 0b10000:
                return InputEvent(type=EventType.TOGGLE_VOICE, source="gauntlet")
            # Hold all pads (3s) = lock
            if pad_mask == 0b11111:
                return InputEvent(type=EventType.LOCK, source="gauntlet")

        return None

    # ── BLE writes ──

    async def _send_mode_update(self) -> None:
        """Write current mode to the Gauntlet's mode_status characteristic."""
        if not self._client or not self._client.is_connected:
            return
        try:
            mode_byte = 0x02 if self._numeric_mode else 0x01
            await self._client.write_gatt_char(
                CHAR_MODE_STATUS, bytes([mode_byte]), response=True
            )
        except Exception as e:
            log.debug(f"Failed to send mode update: {e}")

    async def _write_haptic(self, pattern: HapticPattern) -> None:
        """Write a haptic command to the Gauntlet."""
        if not self._client or not self._client.is_connected:
            return
        try:
            await self._client.write_gatt_char(
                CHAR_HAPTIC_CMD, bytes([pattern]), response=False
            )
        except Exception as e:
            log.debug(f"Failed to send haptic: {e}")
