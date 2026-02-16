"""Connection manager for QR-Link devices.

Routes to the appropriate transport based on the device's protocol.
Maintains a history of known devices for multi-device switching.
Currently supports: MQTT. Future: HTTP/SSE, WebSocket, BLE.
"""

import logging
from typing import Any, Callable

from scouterhud.qrlink.protocol import DeviceLink
from scouterhud.qrlink.transports.mqtt import MQTTTransport

log = logging.getLogger(__name__)

DataCallback = Callable[[dict[str, Any]], None]
MetaCallback = Callable[[dict[str, Any]], None]


class ConnectionManager:
    """Manages active connection and device history for multi-device switching."""

    def __init__(self):
        self._transport: MQTTTransport | None = None
        self._active_link: DeviceLink | None = None
        self._on_data: DataCallback | None = None
        self._on_meta: MetaCallback | None = None

        # Device history for switching (ordered, most recent last)
        self._known_devices: list[DeviceLink] = []
        self._active_index: int = -1

    def connect(
        self,
        link: DeviceLink,
        on_data: DataCallback,
        on_meta: MetaCallback | None = None,
    ) -> bool:
        """Connect to a device. Disconnects any previous connection first."""
        self._on_data = on_data
        self._on_meta = on_meta

        # Disconnect previous if any
        self.disconnect()

        if link.proto == "mqtt":
            transport = MQTTTransport(link)
            if transport.connect(on_data, on_meta):
                self._transport = transport
                self._active_link = link
                self._add_to_history(link)
                log.info(f"Connected to device: {link.id}")
                return True
            else:
                log.error(f"Failed to connect to {link.id}")
                return False
        else:
            log.error(f"Unsupported protocol: {link.proto}")
            return False

    def disconnect(self) -> None:
        if self._transport:
            self._transport.disconnect()
            self._transport = None
            self._active_link = None

    def switch_next(self) -> DeviceLink | None:
        """Switch to next device in history. Returns the DeviceLink or None."""
        if len(self._known_devices) <= 1:
            return None
        self._active_index = (self._active_index + 1) % len(self._known_devices)
        return self._known_devices[self._active_index]

    def switch_prev(self) -> DeviceLink | None:
        """Switch to previous device in history. Returns the DeviceLink or None."""
        if len(self._known_devices) <= 1:
            return None
        self._active_index = (self._active_index - 1) % len(self._known_devices)
        return self._known_devices[self._active_index]

    def reconnect_to(self, link: DeviceLink) -> bool:
        """Reconnect to a specific device from history."""
        if self._on_data is None:
            return False
        return self.connect(link, self._on_data, self._on_meta)

    def _add_to_history(self, link: DeviceLink) -> None:
        """Add device to history, avoiding duplicates."""
        # Remove if already exists (will re-add at end)
        self._known_devices = [d for d in self._known_devices if d.id != link.id]
        self._known_devices.append(link)
        self._active_index = len(self._known_devices) - 1

    @property
    def active_device(self) -> DeviceLink | None:
        return self._active_link

    @property
    def is_connected(self) -> bool:
        return self._transport is not None and self._transport.is_connected

    @property
    def known_devices(self) -> list[DeviceLink]:
        return list(self._known_devices)

    @property
    def device_count(self) -> int:
        return len(self._known_devices)
