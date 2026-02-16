"""MQTT transport for QR-Link connections.

Handles connecting to MQTT broker, fetching $meta, subscribing to data topic,
and streaming data back via a callback.
"""

import json
import logging
import threading
from typing import Any, Callable

import paho.mqtt.client as mqtt

from scouterhud.qrlink.protocol import DeviceLink

log = logging.getLogger(__name__)

DataCallback = Callable[[dict[str, Any]], None]
MetaCallback = Callable[[dict[str, Any]], None]


class MQTTTransport:
    """Manages MQTT connection for a single QR-Link device."""

    def __init__(self, link: DeviceLink):
        self.link = link
        self._client: mqtt.Client | None = None
        self._data_callback: DataCallback | None = None
        self._meta_callback: MetaCallback | None = None
        self._connected = threading.Event()
        self._meta_received = threading.Event()

    def connect(
        self,
        on_data: DataCallback,
        on_meta: MetaCallback | None = None,
        timeout: float = 5.0,
    ) -> bool:
        """Connect to broker, fetch metadata, subscribe to data topic.

        Returns True if connection + meta fetch succeeded.
        """
        self._data_callback = on_data
        self._meta_callback = on_meta

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

        try:
            self._client.connect(self.link.host, self.link.port, keepalive=60)
        except (ConnectionRefusedError, OSError) as e:
            log.error(f"MQTT connect failed: {e}")
            return False

        self._client.loop_start()

        # Wait for connection
        if not self._connected.wait(timeout=timeout):
            log.error("MQTT connection timed out")
            self.disconnect()
            return False

        # Subscribe to $meta first (retained), then data topic
        if self.link.meta_topic:
            self._client.subscribe(self.link.meta_topic, qos=1)

        if self.link.topic:
            self._client.subscribe(self.link.topic, qos=0)

        # Wait for metadata (retained message should arrive quickly)
        if self.link.meta_topic:
            self._meta_received.wait(timeout=3.0)

        return True

    def disconnect(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            log.info(f"Disconnected from {self.link.endpoint}")

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            log.info(f"Connected to MQTT broker {self.link.endpoint}")
            self._connected.set()
        else:
            log.error(f"MQTT connect error: rc={rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        self._connected.clear()
        if rc != 0:
            log.warning(f"MQTT disconnected unexpectedly: rc={rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            log.warning(f"Invalid MQTT message on {msg.topic}: {e}")
            return

        # Route to appropriate callback
        if self.link.meta_topic and msg.topic == self.link.meta_topic:
            log.info(f"Metadata received for {self.link.id}")
            self.link.update_from_metadata(payload)
            if self._meta_callback:
                self._meta_callback(payload)
            self._meta_received.set()
        elif msg.topic == self.link.topic:
            if self._data_callback:
                self._data_callback(payload)
