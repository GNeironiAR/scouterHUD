"""Base class for all virtual QR-Link devices."""

from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlencode


class BaseDevice(ABC):
    """Abstract base for a virtual device that publishes data via MQTT."""

    def __init__(self, config: dict, broker_host: str, broker_port: int):
        self.id: str = config["id"]
        self.name: str = config["name"]
        self.type: str = config["type"]
        self.topic: str = config["topic"]
        self.auth: str = config.get("auth", "open")
        self.pin: str | None = config.get("pin")
        self.token: str | None = config.get("token")
        self.refresh_ms: int = config.get("refresh_ms", 2000)
        self.scenario: str = config.get("scenario", "default")
        self.params: dict = config.get("params", {})
        self.broker_host = broker_host
        self.broker_port = broker_port

        self._setup_generators()

    @abstractmethod
    def _setup_generators(self) -> None:
        """Initialize signal generators based on scenario and params."""

    @abstractmethod
    def generate_data(self) -> dict[str, Any]:
        """Generate one data sample. Returns a flat JSON-serializable dict."""

    @abstractmethod
    def get_icon(self) -> str:
        """Return the icon name for this device type."""

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """Return the data schema for this device's fields."""

    def get_metadata(self) -> dict[str, Any]:
        """Generate the $meta JSON for this device (published as retained)."""
        meta: dict[str, Any] = {
            "v": 1,
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "icon": self.get_icon(),
            "refresh_ms": self.refresh_ms,
            "layout": "auto",
            "schema": self.get_schema(),
        }
        if self.auth == "pin":
            meta["auth_hint"] = "Ingrese el PIN del dispositivo"
        if self.auth == "token":
            meta["auth_hint"] = "Se requiere token de acceso"
        return meta

    def get_qrlink_url(self) -> str:
        """Generate the compact QR-Link URL for this device."""
        base = f"qrlink://v1/{self.id}/mqtt/{self.broker_host}:{self.broker_port}"
        params = {}
        if self.auth != "open":
            params["auth"] = self.auth
        if self.topic:
            params["t"] = self.topic
        if params:
            return f"{base}?{urlencode(params)}"
        return base

    @property
    def meta_topic(self) -> str:
        """MQTT topic for metadata (retained)."""
        return f"{self.topic}/$meta"

    @property
    def refresh_seconds(self) -> float:
        return self.refresh_ms / 1000.0
