"""QR-Link protocol parser.

Parses the compact URL format:
    qrlink://v1/{id}/{proto}/{endpoint}[?auth={auth}&t={topic}]

And validates the result into a DeviceLink dataclass.
"""

import logging
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlparse

log = logging.getLogger(__name__)

SUPPORTED_PROTOS = {"mqtt", "http", "ws", "ble", "mdns"}
SUPPORTED_AUTH = {"open", "pin", "token", "mtls", "mfa"}
PROTOCOL_VERSION = 1


@dataclass
class DeviceLink:
    """Parsed QR-Link device descriptor."""
    version: int
    id: str
    proto: str
    host: str
    port: int
    auth: str = "open"
    topic: str | None = None

    # Populated after metadata fetch
    name: str | None = None
    type: str | None = None
    icon: str | None = None
    refresh_ms: int = 2000
    layout: str = "auto"
    auth_hint: str | None = None
    schema: dict[str, Any] = field(default_factory=dict)

    @property
    def endpoint(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def meta_topic(self) -> str | None:
        """MQTT topic for metadata (retained)."""
        if self.topic:
            return f"{self.topic}/$meta"
        return None

    def update_from_metadata(self, meta: dict[str, Any]) -> None:
        """Update fields from the $meta JSON received from the device."""
        self.name = meta.get("name", self.name)
        self.type = meta.get("type", self.type)
        self.icon = meta.get("icon", self.icon)
        self.refresh_ms = meta.get("refresh_ms", self.refresh_ms)
        self.layout = meta.get("layout", self.layout)
        self.auth_hint = meta.get("auth_hint", self.auth_hint)
        self.schema = meta.get("schema", self.schema)


def parse_qrlink_url(raw: str) -> DeviceLink | None:
    """Parse a qrlink:// URL into a DeviceLink.

    Expected format: qrlink://v1/{id}/{proto}/{host}:{port}[?auth=...&t=...]

    Returns None if the URL is invalid or not a qrlink URL.
    """
    if not raw.startswith("qrlink://"):
        log.debug(f"Not a qrlink URL: {raw[:40]}")
        return None

    try:
        # urlparse treats qrlink as scheme
        parsed = urlparse(raw)
        # path will be: /v1/{id}/{proto}/{host}:{port}
        # netloc will be: v1
        # But urlparse may handle this differently, so let's parse manually

        # Strip scheme
        rest = raw[len("qrlink://"):]

        # Split query string
        if "?" in rest:
            path_part, query_part = rest.split("?", 1)
        else:
            path_part, query_part = rest, ""

        # Parse path segments: v1/{id}/{proto}/{endpoint}
        segments = path_part.split("/")
        if len(segments) < 4:
            log.warning(f"Invalid qrlink URL: not enough segments: {raw}")
            return None

        version_str = segments[0]
        device_id = segments[1]
        proto = segments[2]
        endpoint = "/".join(segments[3:])  # In case endpoint has slashes (unlikely)

        # Parse version
        if not version_str.startswith("v"):
            log.warning(f"Invalid version format: {version_str}")
            return None
        version = int(version_str[1:])

        if version != PROTOCOL_VERSION:
            log.warning(f"Unsupported protocol version: {version}")
            return None

        # Validate proto
        if proto not in SUPPORTED_PROTOS:
            log.warning(f"Unsupported protocol: {proto}")
            return None

        # Parse endpoint (host:port)
        if ":" not in endpoint:
            log.warning(f"Invalid endpoint (missing port): {endpoint}")
            return None

        host, port_str = endpoint.rsplit(":", 1)
        port = int(port_str)

        # Parse query params
        params = parse_qs(query_part)
        auth = params.get("auth", ["open"])[0]
        topic = params.get("t", [None])[0]

        if auth not in SUPPORTED_AUTH:
            log.warning(f"Unknown auth method: {auth}, defaulting to 'open'")
            auth = "open"

        link = DeviceLink(
            version=version,
            id=device_id,
            proto=proto,
            host=host,
            port=port,
            auth=auth,
            topic=topic,
        )

        log.info(f"Parsed QR-Link: {link.id} via {link.proto} @ {link.endpoint}")
        return link

    except (ValueError, IndexError) as e:
        log.warning(f"Failed to parse qrlink URL: {e}")
        return None
