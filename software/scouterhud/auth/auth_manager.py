"""Authentication manager for QR-Link device connections.

Checks the auth level of a DeviceLink and runs the appropriate
authentication flow before allowing data subscription.

Auth levels:
  - "open"  → no auth needed, connect immediately
  - "pin"   → user must enter a numeric PIN via Gauntlet/keyboard
  - "token" → pre-shared token (stored in config file)
"""

import logging
from typing import Any

from scouterhud.qrlink.protocol import DeviceLink

log = logging.getLogger("scouterhud.auth")


class AuthResult:
    """Result of an authentication attempt."""

    def __init__(self, success: bool, credential: str = "", error: str = ""):
        self.success = success
        self.credential = credential  # the PIN/token that was validated
        self.error = error


class AuthManager:
    """Manages authentication for device connections."""

    def __init__(self):
        self._stored_tokens: dict[str, str] = {}  # device_id → token
        self._stored_pins: dict[str, str] = {}     # device_id → PIN (for demo/testing)

    def needs_auth(self, link: DeviceLink) -> bool:
        """Check if a device requires authentication."""
        return link.auth not in ("open", "", None)

    def get_auth_type(self, link: DeviceLink) -> str:
        """Get the authentication type required."""
        return link.auth or "open"

    def validate_pin(self, link: DeviceLink, pin: str) -> AuthResult:
        """Validate a PIN against the device.

        In the real system, this would send the PIN to the device/broker
        and wait for confirmation. For now, we support:
        - Demo PINs from emulator config
        - Stored PINs from previous sessions
        """
        # Demo mode: accept known PINs for emulated devices
        demo_pins = {
            "monitor-bed-12": "1234",
            "press-machine-07": "5678",
        }

        expected = self._stored_pins.get(link.id) or demo_pins.get(link.id)

        if expected is None:
            # No known PIN — in production, send to broker for validation
            log.warning(f"No PIN configured for {link.id}, accepting any PIN")
            return AuthResult(success=True, credential=pin)

        if pin == expected:
            log.info(f"PIN accepted for {link.id}")
            return AuthResult(success=True, credential=pin)

        log.warning(f"Invalid PIN for {link.id}")
        return AuthResult(success=False, error="Invalid PIN")

    def validate_token(self, link: DeviceLink) -> AuthResult:
        """Validate a stored token for the device."""
        token = self._stored_tokens.get(link.id)
        if token:
            log.info(f"Token found for {link.id}")
            return AuthResult(success=True, credential=token)

        log.warning(f"No token stored for {link.id}")
        return AuthResult(success=False, error="No token configured")

    def store_pin(self, device_id: str, pin: str) -> None:
        """Store a PIN for a device (for future connections)."""
        self._stored_pins[device_id] = pin

    def store_token(self, device_id: str, token: str) -> None:
        """Store a token for a device."""
        self._stored_tokens[device_id] = token
