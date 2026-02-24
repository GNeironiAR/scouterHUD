"""PhoneInput — WebSocket backend for phone control.

Runs a WebSocket server that accepts connections from the ScouterApp
web page (app/web/index.html). The phone sends JSON messages for
navigation, numeric entry, and QR-Link URLs. The HUD sends state
updates back to all connected phones.

Also serves the HTML control page via HTTP on the same port.
"""

import asyncio
import json
import logging
import socket
import threading
import time
from collections import deque
from http import HTTPStatus
from pathlib import Path

from scouterhud.input.backend import InputBackend
from scouterhud.input.events import EventType, InputEvent

log = logging.getLogger("scouterhud.input.phone")

# Event name → EventType mapping for incoming messages
_EVENT_MAP: dict[str, EventType] = {
    "nav_up": EventType.NAV_UP,
    "nav_down": EventType.NAV_DOWN,
    "nav_left": EventType.NAV_LEFT,
    "nav_right": EventType.NAV_RIGHT,
    "confirm": EventType.CONFIRM,
    "cancel": EventType.CANCEL,
    "home": EventType.HOME,
    "digit_up": EventType.DIGIT_UP,
    "digit_down": EventType.DIGIT_DOWN,
    "digit_next": EventType.DIGIT_NEXT,
    "digit_prev": EventType.DIGIT_PREV,
    "digit_submit": EventType.DIGIT_SUBMIT,
    "digit_0": EventType.DIGIT_0,
    "digit_1": EventType.DIGIT_1,
    "digit_2": EventType.DIGIT_2,
    "digit_3": EventType.DIGIT_3,
    "digit_4": EventType.DIGIT_4,
    "digit_5": EventType.DIGIT_5,
    "digit_6": EventType.DIGIT_6,
    "digit_7": EventType.DIGIT_7,
    "digit_8": EventType.DIGIT_8,
    "digit_9": EventType.DIGIT_9,
    "digit_backspace": EventType.DIGIT_BACKSPACE,
    "alpha_key": EventType.ALPHA_KEY,
    "alpha_backspace": EventType.ALPHA_BACKSPACE,
    "alpha_enter": EventType.ALPHA_ENTER,
    "alpha_shift": EventType.ALPHA_SHIFT,
    "biometric_auth": EventType.BIOMETRIC_AUTH,
    "next_device": EventType.NEXT_DEVICE,
    "prev_device": EventType.PREV_DEVICE,
    "scan_qr": EventType.SCAN_QR,
    "quit": EventType.QUIT,
}


# Input validation constants (Phase S0)
MAX_MESSAGE_LENGTH = 4096      # bytes per WebSocket message
MAX_QRLINK_URL_LENGTH = 512    # chars for qrlink:// URLs
MAX_AI_CHAT_LENGTH = 1024      # chars for AI chat messages
MAX_MESSAGES_PER_SECOND = 30   # per client rate limit


def _find_html_path() -> Path:
    """Resolve path to app/web/index.html relative to the project root."""
    # software/scouterhud/input/phone_input.py → go up 3 levels to software/
    # then up 1 more to project root, then app/web/index.html
    here = Path(__file__).resolve()
    project_root = here.parents[3]  # scouterHUD/
    return project_root / "app" / "web" / "index.html"


def _get_local_ips() -> list[str]:
    """Get non-loopback IPv4 addresses for this machine."""
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addr = info[4][0]
            if not addr.startswith("127."):
                ips.append(addr)
    except socket.gaierror:
        pass
    # Fallback: connect to a public address to find the default route IP
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
            s.close()
        except OSError:
            pass
    return sorted(set(ips))


class PhoneInput(InputBackend):
    """WebSocket-based input backend for phone control.

    Starts a WebSocket server that:
    - Serves the HTML control page on GET /
    - Accepts WebSocket connections for bidirectional communication
    - Translates incoming JSON events to InputEvent objects
    - Broadcasts HUD state updates to all connected phones
    """

    def __init__(self, port: int = 8765, html_path: str | None = None):
        self._port = port
        self._queue: deque[InputEvent] = deque(maxlen=64)
        self._numeric_mode = False
        self._running = False
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._clients: set = set()
        self._html_bytes: bytes = b""
        self._html_path = Path(html_path) if html_path else _find_html_path()
        # Per-client rate limiting: websocket → list of timestamps
        self._client_msg_times: dict[int, deque] = {}

    @property
    def name(self) -> str:
        return "phone-ws"

    @property
    def numeric_mode(self) -> bool:
        return self._numeric_mode

    @numeric_mode.setter
    def numeric_mode(self, value: bool) -> None:
        self._numeric_mode = value
        self._broadcast({"type": "mode", "numeric": value})

    @property
    def is_available(self) -> bool:
        return self._running

    def start(self) -> None:
        """Load HTML and start WebSocket server in background thread."""
        self._load_html()
        self._running = True
        self._thread = threading.Thread(
            target=self._run_ws_loop,
            name="phone-ws",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the WebSocket server and clean up."""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._clients.clear()

    def poll(self) -> InputEvent | None:
        """Non-blocking poll for the next queued event."""
        if self._queue:
            return self._queue.popleft()
        return None

    def send_state(self, state: str, **kwargs) -> None:
        """Send HUD state update to all connected phones."""
        msg = {"type": "state", "state": state}
        msg.update(kwargs)
        self._broadcast(msg)

    def send_ai_response(self, message: str) -> None:
        """Send AI response message to all connected phones."""
        self._broadcast({"type": "ai_response", "message": message})

    def send_device_list(
        self, devices: list[dict], selected: int, active_id: str
    ) -> None:
        """Send device list data to all connected phones."""
        self._broadcast({
            "type": "device_list",
            "devices": devices,
            "selected": selected,
            "active": active_id,
        })

    # ── Private ──

    def _load_html(self) -> None:
        """Load the HTML control page from disk."""
        try:
            self._html_bytes = self._html_path.read_bytes()
            log.info(f"Loaded control page: {self._html_path}")
        except FileNotFoundError:
            log.warning(f"HTML not found at {self._html_path}, serving fallback")
            self._html_bytes = (
                b"<html><body><h1>ScouterHUD</h1>"
                b"<p>Control page not found. Place index.html in app/web/</p>"
                b"</body></html>"
            )

    def _run_ws_loop(self) -> None:
        """Background thread entry point — runs the asyncio event loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._ws_main())
        except Exception as e:
            if self._running:
                log.error(f"WebSocket server error: {e}")
        finally:
            self._loop.close()
            self._loop = None

    async def _ws_main(self) -> None:
        """Start the WebSocket server and run until stopped."""
        import websockets

        server = await websockets.serve(
            self._handler,
            "0.0.0.0",
            self._port,
            process_request=self._process_request,
            reuse_address=True,
        )

        # Log connection URLs
        for ip in _get_local_ips():
            log.info(f"Phone control: http://{ip}:{self._port}/")
        log.info(f"Phone control: http://localhost:{self._port}/ (local)")

        # Wait until stop() is called
        while self._running:
            await asyncio.sleep(0.5)

        server.close()
        await server.wait_closed()

    def _process_request(self, connection, request):
        """Serve HTML page for regular HTTP GET requests."""
        from websockets.datastructures import Headers
        from websockets.http11 import Response

        # Let WebSocket upgrade requests pass through
        if request.headers.get("Upgrade", "").lower() == "websocket":
            return None

        if request.path in ("/", "/index.html"):
            headers = Headers()
            headers["Content-Type"] = "text/html; charset=utf-8"
            headers["Cache-Control"] = "no-cache"
            # Security headers (Phase S0)
            headers["X-Content-Type-Options"] = "nosniff"
            headers["X-Frame-Options"] = "DENY"
            headers["X-XSS-Protection"] = "1; mode=block"
            headers["Referrer-Policy"] = "no-referrer"
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'unsafe-inline'; "
                "style-src 'unsafe-inline'; "
                "connect-src 'self' ws: wss:; "
                "img-src 'self' data:; "
                "frame-ancestors 'none'"
            )
            return Response(HTTPStatus.OK, "OK", headers, self._html_bytes)
        # Return None for other paths
        return None

    async def _handler(self, websocket) -> None:
        """Handle a WebSocket connection from a phone."""
        self._clients.add(websocket)
        remote = websocket.remote_address
        client_id = id(websocket)
        self._client_msg_times[client_id] = deque(maxlen=MAX_MESSAGES_PER_SECOND)
        log.info(f"Phone connected: {remote}")

        try:
            async for raw in websocket:
                # Input validation: message size limit
                if len(raw) > MAX_MESSAGE_LENGTH:
                    log.warning(f"Phone {remote}: message too large ({len(raw)} bytes), dropped")
                    continue

                # Rate limiting: drop messages if too fast
                now = time.monotonic()
                times = self._client_msg_times.get(client_id)
                if times is not None and len(times) >= MAX_MESSAGES_PER_SECOND:
                    if now - times[0] < 1.0:
                        log.warning(f"Phone {remote}: rate limit exceeded, dropping message")
                        continue
                if times is not None:
                    times.append(now)

                event = self._parse_message(raw)
                if event:
                    self._queue.append(event)
                    log.debug(f"Phone event: {event.type.name}")
        except Exception as e:
            log.debug(f"Phone disconnected: {remote} ({e})")
        finally:
            self._clients.discard(websocket)
            self._client_msg_times.pop(client_id, None)
            log.info(f"Phone disconnected: {remote}")

    def _parse_message(self, raw: str) -> InputEvent | None:
        """Parse a JSON message from the phone into an InputEvent."""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

        msg_type = data.get("type")

        if msg_type == "input":
            event_name = data.get("event", "")
            etype = _EVENT_MAP.get(event_name)
            if etype:
                log.debug(f"Phone input: {event_name} → {etype.name}")
                # Pass through value for events that carry data (e.g. alpha_key)
                value = data.get("value")
                return InputEvent(type=etype, value=value, source="phone")
            else:
                log.warning(f"Phone input: unknown event '{event_name}'")

        elif msg_type == "qrlink":
            url = data.get("url", "")
            if len(url) > MAX_QRLINK_URL_LENGTH:
                log.warning(f"QR-Link URL too long ({len(url)} chars), rejected")
                return None
            if url.startswith("qrlink://"):
                return InputEvent(
                    type=EventType.QRLINK_RECEIVED,
                    value=url,
                    source="phone",
                )

        elif msg_type == "ai_chat":
            message = data.get("message", "")
            if len(message) > MAX_AI_CHAT_LENGTH:
                log.warning(f"AI chat message too long ({len(message)} chars), truncated")
                message = message[:MAX_AI_CHAT_LENGTH]
            if message:
                return InputEvent(
                    type=EventType.AI_CHAT_MESSAGE,
                    value=message,
                    source="phone",
                )

        return None

    def _broadcast(self, msg: dict) -> None:
        """Send a message to all connected phone clients (thread-safe)."""
        if not self._loop or not self._clients:
            return
        text = json.dumps(msg)
        asyncio.run_coroutine_threadsafe(
            self._broadcast_async(text), self._loop
        )

    async def _broadcast_async(self, text: str) -> None:
        """Actually broadcast to all clients (runs in asyncio loop)."""
        import websockets

        websockets.broadcast(self._clients, text)
