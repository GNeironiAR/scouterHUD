"""Authentication manager for QR-Link device connections.

Checks the auth level of a DeviceLink and runs the appropriate
authentication flow before allowing data subscription.

Auth levels:
  - "open"  → no auth needed, connect immediately
  - "pin"   → user must enter a numeric PIN via Gauntlet/keyboard
  - "token" → pre-shared token (stored in config file)

Security (Phase S0):
  - No "accept any PIN" fallback — unknown devices are rejected
  - PINs loaded from config, not hardcoded in source
  - Rate limiting: 5 failed attempts → 15 minute lockout per device
"""

import logging
import time
from typing import Any

from scouterhud.qrlink.protocol import DeviceLink

log = logging.getLogger("scouterhud.auth")

# Rate limiting constants
MAX_PIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 900  # 15 minutes


class AuthResult:
    """Result of an authentication attempt."""

    def __init__(self, success: bool, credential: str = "", error: str = ""):
        self.success = success
        self.credential = credential  # the PIN/token that was validated
        self.error = error


class AuthManager:
    """Manages authentication for device connections."""

    def __init__(self, pins: dict[str, str] | None = None):
        """Initialize with optional PIN mapping.

        Args:
            pins: dict of device_id → PIN. Loaded from config by the caller.
                  If None, no demo/preset PINs are available.
        """
        self._config_pins: dict[str, str] = dict(pins) if pins else {}
        self._stored_tokens: dict[str, str] = {}  # device_id → token
        self._stored_pins: dict[str, str] = {}     # device_id → PIN (runtime overrides)

        # Rate limiting: per-device tracking
        self._failed_attempts: dict[str, int] = {}    # device_id → consecutive failures
        self._lockout_until: dict[str, float] = {}    # device_id → timestamp

    def needs_auth(self, link: DeviceLink) -> bool:
        """Check if a device requires authentication."""
        return link.auth not in ("open", "", None)

    def get_auth_type(self, link: DeviceLink) -> str:
        """Get the authentication type required."""
        return link.auth or "open"

    def is_locked_out(self, device_id: str) -> bool:
        """Check if a device is currently locked out due to failed attempts."""
        lockout_time = self._lockout_until.get(device_id, 0)
        if lockout_time and time.monotonic() < lockout_time:
            return True
        # Lockout expired — clear it
        if lockout_time:
            self._lockout_until.pop(device_id, None)
            self._failed_attempts.pop(device_id, None)
        return False

    def get_lockout_remaining(self, device_id: str) -> int:
        """Seconds remaining in lockout, or 0 if not locked out."""
        lockout_time = self._lockout_until.get(device_id, 0)
        if lockout_time:
            remaining = lockout_time - time.monotonic()
            if remaining > 0:
                return int(remaining)
        return 0

    def validate_pin(self, link: DeviceLink, pin: str) -> AuthResult:
        """Validate a PIN against the device.

        Security:
        - Rejects unknown devices (no fallback to "accept any")
        - Enforces rate limiting (5 attempts → 15 min lockout)
        - PINs come from config, not hardcoded
        """
        # Check lockout first
        if self.is_locked_out(link.id):
            remaining = self.get_lockout_remaining(link.id)
            log.warning(f"Device {link.id} is locked out for {remaining}s")
            return AuthResult(
                success=False,
                error=f"Locked out. Try again in {remaining // 60 + 1} min",
            )

        # Look up expected PIN: runtime override > config
        expected = self._stored_pins.get(link.id) or self._config_pins.get(link.id)

        if expected is None:
            log.warning(f"No PIN configured for {link.id}, rejecting")
            return AuthResult(success=False, error="No PIN configured for this device")

        if pin == expected:
            log.info(f"PIN accepted for {link.id}")
            # Clear failed attempts on success
            self._failed_attempts.pop(link.id, None)
            self._lockout_until.pop(link.id, None)
            return AuthResult(success=True, credential=pin)

        # Failed attempt — track and possibly lock out
        failures = self._failed_attempts.get(link.id, 0) + 1
        self._failed_attempts[link.id] = failures
        log.warning(f"Invalid PIN for {link.id} (attempt {failures}/{MAX_PIN_ATTEMPTS})")

        if failures >= MAX_PIN_ATTEMPTS:
            self._lockout_until[link.id] = time.monotonic() + LOCKOUT_SECONDS
            log.warning(f"Device {link.id} locked out for {LOCKOUT_SECONDS}s after {failures} failed attempts")
            return AuthResult(
                success=False,
                error=f"Too many attempts. Locked for {LOCKOUT_SECONDS // 60} min",
            )

        remaining = MAX_PIN_ATTEMPTS - failures
        return AuthResult(success=False, error=f"Invalid PIN ({remaining} attempts left)")

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
