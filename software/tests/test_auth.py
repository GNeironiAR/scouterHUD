"""Tests for auth manager and PIN entry."""

import time

import pytest

from scouterhud.auth.auth_manager import (
    AuthManager, AuthResult, LOCKOUT_SECONDS, MAX_PIN_ATTEMPTS,
)
from scouterhud.auth.pin_entry import PinEntry
from scouterhud.input.events import EventType, InputEvent
from scouterhud.qrlink.protocol import DeviceLink


DEMO_PINS = {
    "monitor-bed-12": "1234",
    "press-machine-07": "5678",
}


def _make_link(**kwargs):
    defaults = dict(version=1, id="test-01", proto="mqtt", host="localhost", port=1883)
    defaults.update(kwargs)
    return DeviceLink(**defaults)


def _event(etype: EventType) -> InputEvent:
    return InputEvent(type=etype, source="test")


class TestAuthManager:
    """Tests for AuthManager."""

    def test_open_auth_no_auth_needed(self):
        am = AuthManager()
        link = _make_link(auth="open")
        assert am.needs_auth(link) is False

    def test_empty_auth_no_auth_needed(self):
        am = AuthManager()
        link = _make_link(auth="")
        assert am.needs_auth(link) is False

    def test_pin_auth_needs_auth(self):
        am = AuthManager()
        link = _make_link(auth="pin")
        assert am.needs_auth(link) is True

    def test_token_auth_needs_auth(self):
        am = AuthManager()
        link = _make_link(auth="token")
        assert am.needs_auth(link) is True

    def test_get_auth_type(self):
        am = AuthManager()
        assert am.get_auth_type(_make_link(auth="pin")) == "pin"
        assert am.get_auth_type(_make_link(auth="open")) == "open"
        assert am.get_auth_type(_make_link(auth="token")) == "token"

    def test_validate_pin_correct(self):
        am = AuthManager(pins=DEMO_PINS)
        link = _make_link(id="monitor-bed-12", auth="pin")
        result = am.validate_pin(link, "1234")
        assert result.success is True
        assert result.credential == "1234"

    def test_validate_pin_wrong(self):
        am = AuthManager(pins=DEMO_PINS)
        link = _make_link(id="monitor-bed-12", auth="pin")
        result = am.validate_pin(link, "0000")
        assert result.success is False
        assert "Invalid PIN" in result.error

    def test_validate_second_demo_pin(self):
        am = AuthManager(pins=DEMO_PINS)
        link = _make_link(id="press-machine-07", auth="pin")
        result = am.validate_pin(link, "5678")
        assert result.success is True

    def test_unknown_device_rejects_pin(self):
        """Phase S0: unknown devices are rejected (no 'accept any' fallback)."""
        am = AuthManager(pins=DEMO_PINS)
        link = _make_link(id="unknown-device", auth="pin")
        result = am.validate_pin(link, "9999")
        assert result.success is False
        assert "No PIN configured" in result.error

    def test_no_pins_configured_rejects_all(self):
        """AuthManager with no pins rejects everything."""
        am = AuthManager()
        link = _make_link(id="monitor-bed-12", auth="pin")
        result = am.validate_pin(link, "1234")
        assert result.success is False

    def test_stored_pin_overrides_config(self):
        am = AuthManager(pins=DEMO_PINS)
        am.store_pin("monitor-bed-12", "4321")
        link = _make_link(id="monitor-bed-12", auth="pin")

        assert am.validate_pin(link, "4321").success is True
        assert am.validate_pin(link, "1234").success is False

    def test_validate_token_found(self):
        am = AuthManager()
        am.store_token("srv-01", "abc123")
        link = _make_link(id="srv-01", auth="token")
        result = am.validate_token(link)
        assert result.success is True
        assert result.credential == "abc123"

    def test_validate_token_not_found(self):
        am = AuthManager()
        link = _make_link(id="srv-01", auth="token")
        result = am.validate_token(link)
        assert result.success is False


class TestPinRateLimiting:
    """Tests for PIN rate limiting (Phase S0)."""

    def test_failed_attempts_counted(self):
        am = AuthManager(pins={"dev-1": "1234"})
        link = _make_link(id="dev-1", auth="pin")

        result = am.validate_pin(link, "0000")
        assert result.success is False
        assert f"{MAX_PIN_ATTEMPTS - 1} attempts left" in result.error

    def test_lockout_after_max_attempts(self):
        am = AuthManager(pins={"dev-1": "1234"})
        link = _make_link(id="dev-1", auth="pin")

        for i in range(MAX_PIN_ATTEMPTS):
            result = am.validate_pin(link, "0000")
            assert result.success is False

        # Should now be locked out
        assert am.is_locked_out("dev-1") is True

        # Next attempt should fail with lockout message
        result = am.validate_pin(link, "1234")  # even correct PIN
        assert result.success is False
        assert "Locked out" in result.error

    def test_successful_pin_clears_attempts(self):
        am = AuthManager(pins={"dev-1": "1234"})
        link = _make_link(id="dev-1", auth="pin")

        # Fail a few times
        for _ in range(3):
            am.validate_pin(link, "0000")

        # Succeed
        result = am.validate_pin(link, "1234")
        assert result.success is True

        # Counter should be reset — next failure starts from 0
        result = am.validate_pin(link, "0000")
        assert f"{MAX_PIN_ATTEMPTS - 1} attempts left" in result.error

    def test_lockout_per_device(self):
        am = AuthManager(pins={"dev-1": "1111", "dev-2": "2222"})
        link1 = _make_link(id="dev-1", auth="pin")
        link2 = _make_link(id="dev-2", auth="pin")

        # Lock out dev-1
        for _ in range(MAX_PIN_ATTEMPTS):
            am.validate_pin(link1, "0000")

        assert am.is_locked_out("dev-1") is True
        assert am.is_locked_out("dev-2") is False

        # dev-2 should still work
        result = am.validate_pin(link2, "2222")
        assert result.success is True

    def test_lockout_remaining_seconds(self):
        am = AuthManager(pins={"dev-1": "1234"})
        link = _make_link(id="dev-1", auth="pin")

        for _ in range(MAX_PIN_ATTEMPTS):
            am.validate_pin(link, "0000")

        remaining = am.get_lockout_remaining("dev-1")
        assert remaining > 0
        assert remaining <= LOCKOUT_SECONDS

    def test_no_lockout_when_not_locked(self):
        am = AuthManager(pins={"dev-1": "1234"})
        assert am.is_locked_out("dev-1") is False
        assert am.get_lockout_remaining("dev-1") == 0


class TestPinEntry:
    """Tests for PinEntry UI logic."""

    def test_initial_state(self):
        pe = PinEntry(pin_length=4, device_name="Test")
        assert pe.pin_value == "0000"
        assert pe.is_done is False
        assert pe.was_cancelled is False

    def test_digit_up_increments(self):
        pe = PinEntry()
        pe.handle_event(_event(EventType.DIGIT_UP))
        assert pe.pin_value == "1000"

    def test_digit_down_decrements_wraps(self):
        pe = PinEntry()
        pe.handle_event(_event(EventType.DIGIT_DOWN))
        assert pe.pin_value == "9000"

    def test_digit_up_wraps_at_9(self):
        pe = PinEntry()
        for _ in range(10):
            pe.handle_event(_event(EventType.DIGIT_UP))
        assert pe.pin_value == "0000"

    def test_navigate_and_change_digits(self):
        pe = PinEntry()
        # Set digit 0 to 1
        pe.handle_event(_event(EventType.DIGIT_UP))
        # Move to digit 1
        pe.handle_event(_event(EventType.DIGIT_NEXT))
        # Set digit 1 to 2
        pe.handle_event(_event(EventType.DIGIT_UP))
        pe.handle_event(_event(EventType.DIGIT_UP))
        # Move to digit 2
        pe.handle_event(_event(EventType.DIGIT_NEXT))
        # Set digit 2 to 3
        for _ in range(3):
            pe.handle_event(_event(EventType.DIGIT_UP))
        # Move to digit 3
        pe.handle_event(_event(EventType.DIGIT_NEXT))
        # Set digit 3 to 4
        for _ in range(4):
            pe.handle_event(_event(EventType.DIGIT_UP))

        assert pe.pin_value == "1234"

    def test_nav_events_work_as_digit_events(self):
        pe = PinEntry()
        pe.handle_event(_event(EventType.NAV_UP))
        assert pe.pin_value == "1000"

        pe.handle_event(_event(EventType.NAV_RIGHT))
        pe.handle_event(_event(EventType.NAV_DOWN))
        assert pe.pin_value == "1900"

    def test_cursor_clamps_at_boundaries(self):
        pe = PinEntry(pin_length=4)
        # Move left past 0 — should stay at 0
        pe.handle_event(_event(EventType.DIGIT_PREV))
        pe.handle_event(_event(EventType.DIGIT_UP))
        assert pe.pin_value == "1000"  # still on digit 0

        # Move right past end
        for _ in range(10):
            pe.handle_event(_event(EventType.DIGIT_NEXT))
        pe.handle_event(_event(EventType.DIGIT_UP))
        assert pe.pin_value == "1001"  # on digit 3

    def test_submit(self):
        pe = PinEntry()
        pe.handle_event(_event(EventType.DIGIT_SUBMIT))
        assert pe.is_done is True
        assert pe.was_cancelled is False

    def test_confirm_also_submits(self):
        pe = PinEntry()
        pe.handle_event(_event(EventType.CONFIRM))
        assert pe.is_done is True

    def test_cancel(self):
        pe = PinEntry()
        pe.handle_event(_event(EventType.CANCEL))
        assert pe.is_done is True
        assert pe.was_cancelled is True

    def test_set_error_resets_for_retry(self):
        pe = PinEntry()
        pe.handle_event(_event(EventType.DIGIT_UP))
        pe.handle_event(_event(EventType.CONFIRM))

        pe.set_error("Invalid PIN")
        assert pe.is_done is False  # reset
        assert pe.pin_value == "0000"  # digits reset

    def test_render_returns_image(self):
        pe = PinEntry(pin_length=4, device_name="Test Device")
        img = pe.render()
        assert img.size == (240, 240)
        assert img.mode == "RGB"

    def test_render_with_error(self):
        pe = PinEntry()
        pe.set_error("Wrong PIN")
        img = pe.render()
        assert img.size == (240, 240)

    def test_attempt_counter(self):
        pe = PinEntry()
        assert pe._attempts == 0
        pe.handle_event(_event(EventType.CONFIRM))
        assert pe._attempts == 1
        pe.set_error("Nope")
        pe.handle_event(_event(EventType.CONFIRM))
        assert pe._attempts == 2
