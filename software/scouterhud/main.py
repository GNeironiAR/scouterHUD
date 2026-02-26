#!/usr/bin/env python3
"""ScouterHUD — Main entry point.

App state machine:
  SCANNING    → waiting for QR scan
  AUTH        → PIN entry required before connecting
  CONNECTING  → establishing MQTT connection
  STREAMING   → showing live device data
  DEVICE_LIST → browsing known devices
  ERROR       → showing error, returns to previous state

Modes:
  --scan <qr_image>    Scan a QR image file, connect to device, show live data
  --demo <device_id>   Connect directly to an emulated device (no QR scan needed)
  --phone [PORT]       Start WebSocket server for phone control (default: 8765)

Display:
  --preview            Use PNG file backend (for WSL2 / headless)
  --spi                Use SPI display backend (ST7789 on Raspberry Pi)
  (default)            Use pygame window

Usage:
    python -m scouterhud.main --preview --demo monitor-bed-12 --broker localhost:1883 --topic ward3/bed12/vitals
    python -m scouterhud.main --preview --phone
    python -m scouterhud.main --preview --phone --demo monitor-bed-12 --broker localhost:1883 --topic ward3/bed12/vitals
"""

import argparse
import logging
import threading
import time
from enum import Enum, auto
from typing import Any

from scouterhud.auth.auth_manager import AuthManager
from scouterhud.auth.pin_entry import PinEntry
from scouterhud.camera.backend_desktop import DesktopCameraBackend
from scouterhud.camera.qr_decoder import scan_qr
from scouterhud.display.backend import DisplayBackend
from scouterhud.display.backend_desktop import DesktopBackend
from scouterhud.display.backend_preview import PreviewBackend
from scouterhud.display.renderer import (
    render_connecting_screen,
    render_device_list,
    render_error_screen,
    render_frame,
    render_scanning_screen,
)
from scouterhud.input.events import EventType
from scouterhud.input.input_manager import InputManager
from scouterhud.input.keyboard_input import KeyboardInput, StdinKeyboardInput
from scouterhud.qrlink.connection import ConnectionManager
from scouterhud.qrlink.protocol import DeviceLink, parse_qrlink_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scouterhud")


class AppState(Enum):
    SCANNING = auto()
    AUTH = auto()
    CONNECTING = auto()
    STREAMING = auto()
    DEVICE_LIST = auto()
    ERROR = auto()


class ScouterHUD:
    """Main application controller with state machine."""

    def __init__(
        self,
        use_preview: bool = False,
        use_spi: bool = False,
        spi_speed: int = 40_000_000,
        rotation: int = 0,
        phone_port: int | None = None,
    ):
        # Display
        if use_spi:
            from scouterhud.display.backend_spi import SPIBackend

            self.display: DisplayBackend = SPIBackend(
                spi_speed_hz=spi_speed, rotation=rotation,
            )
        elif use_preview:
            self.display = PreviewBackend()
        else:
            self.display = DesktopBackend(scale=3, title="ScouterHUD")

        # Input
        self.input = InputManager()
        if use_spi or use_preview:
            self.input.add_backend(StdinKeyboardInput())
        else:
            self.input.add_backend(KeyboardInput())

        # Phone input (optional WebSocket server)
        self._phone_input = None
        if phone_port is not None:
            from scouterhud.input.phone_input import PhoneInput

            self._phone_input = PhoneInput(port=phone_port)
            self.input.add_backend(self._phone_input)

        # Core systems
        self.connection = ConnectionManager()
        self.auth = AuthManager(pins=self._load_demo_pins())

        # State
        self._state = AppState.SCANNING
        self._latest_data: dict[str, Any] | None = None
        self._data_lock = threading.Lock()
        self._running = True
        self._error_msg = ""
        self._error_return_state = AppState.SCANNING

        # PIN entry
        self._pin_entry: PinEntry | None = None
        self._pending_link: DeviceLink | None = None

        # Device list
        self._device_list_index = 0

        # Sensor broadcast throttle (max 1 Hz to phone)
        self._last_sensor_broadcast = 0.0

    @staticmethod
    def _load_demo_pins() -> dict[str, str]:
        """Load device PINs from emulator config.yaml (if available)."""
        from pathlib import Path

        config_path = Path(__file__).resolve().parents[2] / "emulator" / "config.yaml"
        if not config_path.exists():
            log.debug("No emulator config.yaml found, no demo PINs loaded")
            return {}

        try:
            import yaml
        except ImportError:
            log.debug("PyYAML not available, no demo PINs loaded")
            return {}

        try:
            data = yaml.safe_load(config_path.read_text())
            pins = {}
            for dev in data.get("devices", []):
                if dev.get("pin"):
                    pins[dev["id"]] = str(dev["pin"])
            if pins:
                log.info(f"Loaded {len(pins)} device PINs from emulator config")
            return pins
        except Exception as e:
            log.warning(f"Failed to load emulator config: {e}")
            return {}

    # ── Public entry points ──

    def run_scan(self, qr_image_path: str) -> None:
        """Scan a QR image file, connect, and show live data."""
        log.info(f"Scanning QR from: {qr_image_path}")
        self._set_state(AppState.SCANNING)
        self.display.show(render_scanning_screen())

        camera = DesktopCameraBackend(qr_image_path=qr_image_path)
        camera.start()

        if not camera.is_available():
            self._show_error(f"File not found: {qr_image_path}", AppState.SCANNING)
            self._run_loop()
            return

        frame = camera.capture_frame()
        camera.stop()

        raw_qr = scan_qr(frame)
        if not raw_qr:
            self._show_error("No QR code found in image", AppState.SCANNING)
            self._run_loop()
            return

        link = parse_qrlink_url(raw_qr)
        if not link:
            self._show_error("Invalid QR-Link URL", AppState.SCANNING)
            self._run_loop()
            return

        self._initiate_connection(link)
        self._run_loop()

    def run_demo(self, device_id: str, broker: str, topic: str, auth: str = "open") -> None:
        """Connect directly to a device without QR scanning."""
        host, port_str = broker.split(":")
        port = int(port_str)

        link = DeviceLink(
            version=1,
            id=device_id,
            proto="mqtt",
            host=host,
            port=port,
            auth=auth,
            topic=topic,
        )

        self._initiate_connection(link)
        self._run_loop()

    def run_phone(self) -> None:
        """Start in SCANNING state, wait for phone to send QR-Link URL."""
        log.info("Waiting for phone connection...")
        self._set_state(AppState.SCANNING)
        self._run_loop()

    # ── Connection flow ──

    def _set_state(self, new_state: AppState) -> None:
        """Transition to a new state and notify connected phones."""
        self._state = new_state
        if self._phone_input:
            kwargs: dict[str, Any] = {}
            if new_state == AppState.STREAMING and self.connection.active_device:
                kwargs["device"] = self.connection.active_device.id
            elif new_state == AppState.ERROR:
                kwargs["error"] = self._error_msg
            self._phone_input.send_state(new_state.name.lower(), **kwargs)
            if new_state == AppState.DEVICE_LIST:
                self._send_device_list()

    def _send_device_list(self) -> None:
        """Send current device list to phone app."""
        if not self._phone_input:
            return
        devices = self.connection.known_devices
        active = self.connection.active_device
        active_id = active.id if active else ""
        device_data = []
        for d in devices:
            device_data.append({
                "id": d.id,
                "name": d.name or d.id,
                "type": d.type or "unknown",
                "auth": d.auth or "open",
            })
        self._phone_input.send_device_list(
            device_data, self._device_list_index, active_id
        )

    def _initiate_connection(self, link: DeviceLink) -> None:
        """Start connection flow: check auth, then connect."""
        if self.auth.needs_auth(link):
            self._pending_link = link
            self._pin_entry = PinEntry(
                pin_length=4,
                device_name=link.name or link.id,
            )
            self._set_state(AppState.AUTH)
            self.input.set_numeric_mode(True)
            log.info(f"Auth required for {link.id} (type: {link.auth})")
        else:
            self._do_connect(link)

    def _do_connect(self, link: DeviceLink) -> None:
        """Actually connect to the device."""
        self._set_state(AppState.CONNECTING)
        self.display.show(render_connecting_screen(link.id))

        success = self.connection.connect(
            link,
            on_data=self._on_data,
            on_meta=self._on_meta,
        )

        if success:
            self._set_state(AppState.STREAMING)
            self._latest_data = None
            log.info(f"Connected! Streaming data from {link.id}")
        else:
            self._show_error(
                f"Cannot connect to {link.endpoint}. Is the broker running?",
                AppState.SCANNING,
            )

    # ── Main loop ──

    def _run_loop(self) -> None:
        """Main event + render loop."""
        self.input.start()

        try:
            while self._running:
                # Handle input
                event = self.input.poll()
                if event:
                    self._handle_event(event)

                # Render current state
                self._render()

                time.sleep(0.05)  # ~20 FPS

        except KeyboardInterrupt:
            log.info("Shutting down...")
        finally:
            self.input.stop()
            self.connection.disconnect()
            self.display.close()

    # ── Event handling ──

    def _handle_event(self, event) -> None:
        """Route input event to the current state handler."""
        if event.type == EventType.QUIT:
            self._running = False
            return

        # AI chat messages are handled globally (any state)
        if event.type == EventType.AI_CHAT_MESSAGE:
            self._handle_ai_chat(event)
            return

        handler = {
            AppState.SCANNING: self._handle_scanning_event,
            AppState.AUTH: self._handle_auth_event,
            AppState.STREAMING: self._handle_streaming_event,
            AppState.DEVICE_LIST: self._handle_device_list_event,
            AppState.ERROR: self._handle_error_event,
        }.get(self._state)

        if handler:
            handler(event)

    def _handle_scanning_event(self, event) -> None:
        """Handle events while waiting for QR scan (phone mode)."""
        if event.type == EventType.QRLINK_RECEIVED:
            url = event.value
            link = parse_qrlink_url(url)
            if link:
                log.info(f"QR-Link received from {event.source}: {link.id}")
                self._initiate_connection(link)
            else:
                self._show_error("Invalid QR-Link URL", AppState.SCANNING)

    def _handle_auth_event(self, event) -> None:
        """Handle events during PIN entry."""
        if not self._pin_entry or not self._pending_link:
            return

        # Biometric auth bypasses PIN
        if event.type == EventType.BIOMETRIC_AUTH:
            if event.value == "success":
                log.info(f"Biometric auth accepted for {self._pending_link.id}")
                self.input.set_numeric_mode(False)
                link = self._pending_link
                self._pin_entry = None
                self._pending_link = None
                self._do_connect(link)
            else:
                log.warning("Biometric auth failed, PIN entry continues")
            return

        self._pin_entry.handle_event(event)

        if self._pin_entry.was_cancelled:
            self.input.set_numeric_mode(False)
            self._pin_entry = None
            self._pending_link = None
            self._set_state(AppState.SCANNING)
            log.info("PIN entry cancelled")

        elif self._pin_entry.is_done:
            result = self.auth.validate_pin(self._pending_link, self._pin_entry.pin_value)
            if result.success:
                self.input.set_numeric_mode(False)
                link = self._pending_link
                self._pin_entry = None
                self._pending_link = None
                self._do_connect(link)
            else:
                self._pin_entry.set_error(result.error)

    def _handle_streaming_event(self, event) -> None:
        """Handle events while streaming data."""
        if event.type == EventType.NEXT_DEVICE:
            next_link = self.connection.switch_next()
            if next_link:
                log.info(f"Switching to next device: {next_link.id}")
                self._initiate_connection(next_link)

        elif event.type == EventType.PREV_DEVICE:
            prev_link = self.connection.switch_prev()
            if prev_link:
                log.info(f"Switching to previous device: {prev_link.id}")
                self._initiate_connection(prev_link)

        elif event.type == EventType.NAV_LEFT:
            prev_link = self.connection.switch_prev()
            if prev_link:
                log.info(f"D-pad left → switching to previous device: {prev_link.id}")
                self._initiate_connection(prev_link)

        elif event.type == EventType.NAV_RIGHT:
            next_link = self.connection.switch_next()
            if next_link:
                log.info(f"D-pad right → switching to next device: {next_link.id}")
                self._initiate_connection(next_link)

        elif event.type == EventType.HOME:
            if self.connection.device_count > 0:
                self._device_list_index = 0
                self._set_state(AppState.DEVICE_LIST)

        elif event.type == EventType.CANCEL:
            self.connection.disconnect()
            self._set_state(AppState.SCANNING)

    def _handle_device_list_event(self, event) -> None:
        """Handle events in device list screen."""
        devices = self.connection.known_devices

        if event.type == EventType.NAV_UP:
            self._device_list_index = max(0, self._device_list_index - 1)
            self._send_device_list()

        elif event.type == EventType.NAV_DOWN:
            self._device_list_index = min(len(devices) - 1, self._device_list_index + 1)
            self._send_device_list()

        elif event.type == EventType.CONFIRM:
            if devices:
                selected = devices[self._device_list_index]
                self._initiate_connection(selected)

        elif event.type == EventType.CANCEL:
            self._set_state(AppState.STREAMING)

    def _handle_error_event(self, event) -> None:
        """Any key press on error screen returns to previous state."""
        if event.type in (EventType.CONFIRM, EventType.CANCEL):
            self._set_state(self._error_return_state)

    def _handle_ai_chat(self, event) -> None:
        """Handle AI chat message from phone. Stub: echo back a placeholder."""
        message = event.value or ""
        log.info(f"AI chat from {event.source}: {message}")
        if self._phone_input:
            self._phone_input.send_ai_response(
                f"AI coming soon. You said: \"{message}\""
            )

    # ── Rendering ──

    def _render(self) -> None:
        """Render frame for the current app state."""
        if self._state == AppState.SCANNING:
            self.display.show(render_scanning_screen())

        elif self._state == AppState.AUTH:
            if self._pin_entry:
                self.display.show(self._pin_entry.render())

        elif self._state == AppState.CONNECTING:
            pass  # already rendered in _do_connect

        elif self._state == AppState.STREAMING:
            with self._data_lock:
                data = self._latest_data

            if data and self.connection.active_device:
                frame = render_frame(self.connection.active_device, data)
                self.display.show(frame)

                # Send sensor data to phone (throttled to 1 Hz)
                now = time.monotonic()
                if self._phone_input and now - self._last_sensor_broadcast >= 1.0:
                    self._last_sensor_broadcast = now
                    device = self.connection.active_device
                    self._phone_input.send_sensor_data(
                        device_id=device.id,
                        device_name=device.name,
                        device_type=device.type,
                        data=data,
                        schema=device.schema,
                    )
            elif self.connection.active_device:
                device_id = self.connection.active_device.id
                self.display.show(render_connecting_screen(device_id))

        elif self._state == AppState.DEVICE_LIST:
            active_id = self.connection.active_device.id if self.connection.active_device else ""
            frame = render_device_list(
                self.connection.known_devices,
                self._device_list_index,
                active_id,
            )
            self.display.show(frame)

        elif self._state == AppState.ERROR:
            self.display.show(render_error_screen(self._error_msg))

    # ── Callbacks ──

    def _on_data(self, data: dict[str, Any]) -> None:
        with self._data_lock:
            self._latest_data = data

    def _on_meta(self, meta: dict[str, Any]) -> None:
        log.info(f"Device metadata: name={meta.get('name')}, type={meta.get('type')}")

    def _show_error(self, msg: str, return_state: AppState) -> None:
        self._error_msg = msg
        self._error_return_state = return_state
        self._set_state(AppState.ERROR)
        log.error(msg)


def main():
    parser = argparse.ArgumentParser(
        description="ScouterHUD — AI-Powered Monocular HUD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Preview mode (WSL2) - scan QR from file
  python -m scouterhud.main --preview --scan ../emulator/qr_output/monitor-bed-12.png

  # Preview mode - direct connection
  python -m scouterhud.main --preview --demo monitor-bed-12 --broker localhost:1883 --topic ward3/bed12/vitals

  # Phone control mode - open http://<your-ip>:8765/ on your phone
  python -m scouterhud.main --preview --phone

  # Phone + demo mode - phone as additional control
  python -m scouterhud.main --preview --phone --demo monitor-bed-12 --broker localhost:1883 --topic ward3/bed12/vitals

Controls (preview: w/a/s/d, enter, x, q | pygame: arrows, enter, escape):
  Navigate / change PIN digits    arrows or w/a/s/d
  Confirm / submit                Enter
  Cancel / back                   Escape or x
  Device list                     H (while streaming)
  Next / previous device          N / P
  Quit                            Q
        """,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--scan", metavar="QR_IMAGE", help="Scan QR from image file")
    mode.add_argument("--demo", metavar="DEVICE_ID", help="Connect directly by device ID")

    parser.add_argument("--broker", default="localhost:1883", help="MQTT broker host:port")
    parser.add_argument("--topic", help="MQTT topic (required for --demo)")
    parser.add_argument("--auth", default="open", help="Auth method (default: open)")
    parser.add_argument(
        "--preview", action="store_true",
        help="Use file-based preview backend (saves PNG to /tmp/scouterhud_live.png)",
    )
    parser.add_argument(
        "--spi", action="store_true",
        help="Use SPI display backend (ST7789 on Raspberry Pi)",
    )
    parser.add_argument(
        "--spi-speed", type=int, default=40_000_000,
        help="SPI bus speed in Hz (default: 40000000)",
    )
    parser.add_argument(
        "--rotation", type=int, default=0, choices=[0, 1, 2, 3],
        help="Display rotation: 0, 1 (90°), 2 (180°), 3 (270°)",
    )
    parser.add_argument(
        "--phone", nargs="?", const=8765, type=int, metavar="PORT",
        help="Enable phone WebSocket control (default port: 8765)",
    )

    args = parser.parse_args()

    if args.preview and args.spi:
        parser.error("--preview and --spi are mutually exclusive")

    if not args.scan and not args.demo and args.phone is None:
        parser.error("At least one of --scan, --demo, or --phone is required")

    hud = ScouterHUD(
        use_preview=args.preview,
        use_spi=args.spi,
        spi_speed=args.spi_speed,
        rotation=args.rotation,
        phone_port=args.phone,
    )

    if args.spi:
        log.info("SPI display mode (ST7789 240x240)")
        log.info("Controls: w/a/s/d=navigate, enter=confirm, x=cancel, h=devices, n/p=switch, q=quit")
    elif args.preview:
        log.info(f"Preview mode: open {hud.display.output_path} in VSCode")
        log.info("Controls: w/a/s/d=navigate, enter=confirm, x=cancel, h=devices, n/p=switch, q=quit")

    if args.scan:
        hud.run_scan(args.scan)
    elif args.demo:
        if not args.topic:
            parser.error("--topic is required with --demo")
        hud.run_demo(args.demo, args.broker, args.topic, args.auth)
    elif args.phone is not None:
        hud.run_phone()


if __name__ == "__main__":
    main()
