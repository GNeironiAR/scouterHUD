"""Tests for PhoneInput WebSocket backend."""

import json

import pytest

from scouterhud.input.events import EventType, InputEvent
from scouterhud.input.phone_input import PhoneInput, _EVENT_MAP


class TestPhoneInputProperties:
    """Test backend properties (no network needed)."""

    def test_name(self):
        pi = PhoneInput()
        assert pi.name == "phone-ws"

    def test_default_port(self):
        pi = PhoneInput()
        assert pi._port == 8765

    def test_custom_port(self):
        pi = PhoneInput(port=9000)
        assert pi._port == 9000

    def test_not_available_before_start(self):
        pi = PhoneInput()
        assert pi.is_available is False

    def test_poll_empty(self):
        pi = PhoneInput()
        assert pi.poll() is None

    def test_numeric_mode_default_false(self):
        pi = PhoneInput()
        assert pi.numeric_mode is False

    def test_numeric_mode_setter(self):
        pi = PhoneInput()
        # Directly set internal state (no WS server running)
        pi._numeric_mode = True
        assert pi.numeric_mode is True


class TestMessageParsing:
    """Test _parse_message() (pure function, no network)."""

    def setup_method(self):
        self.pi = PhoneInput()

    def test_nav_up(self):
        e = self.pi._parse_message('{"type": "input", "event": "nav_up"}')
        assert e is not None
        assert e.type == EventType.NAV_UP
        assert e.source == "phone"

    def test_nav_down(self):
        e = self.pi._parse_message('{"type": "input", "event": "nav_down"}')
        assert e.type == EventType.NAV_DOWN

    def test_nav_left(self):
        e = self.pi._parse_message('{"type": "input", "event": "nav_left"}')
        assert e.type == EventType.NAV_LEFT

    def test_nav_right(self):
        e = self.pi._parse_message('{"type": "input", "event": "nav_right"}')
        assert e.type == EventType.NAV_RIGHT

    def test_confirm(self):
        e = self.pi._parse_message('{"type": "input", "event": "confirm"}')
        assert e.type == EventType.CONFIRM

    def test_cancel(self):
        e = self.pi._parse_message('{"type": "input", "event": "cancel"}')
        assert e.type == EventType.CANCEL

    def test_home(self):
        e = self.pi._parse_message('{"type": "input", "event": "home"}')
        assert e.type == EventType.HOME

    def test_digit_up(self):
        e = self.pi._parse_message('{"type": "input", "event": "digit_up"}')
        assert e.type == EventType.DIGIT_UP

    def test_digit_down(self):
        e = self.pi._parse_message('{"type": "input", "event": "digit_down"}')
        assert e.type == EventType.DIGIT_DOWN

    def test_digit_next(self):
        e = self.pi._parse_message('{"type": "input", "event": "digit_next"}')
        assert e.type == EventType.DIGIT_NEXT

    def test_digit_prev(self):
        e = self.pi._parse_message('{"type": "input", "event": "digit_prev"}')
        assert e.type == EventType.DIGIT_PREV

    def test_digit_submit(self):
        e = self.pi._parse_message('{"type": "input", "event": "digit_submit"}')
        assert e.type == EventType.DIGIT_SUBMIT

    def test_next_device(self):
        e = self.pi._parse_message('{"type": "input", "event": "next_device"}')
        assert e.type == EventType.NEXT_DEVICE

    def test_prev_device(self):
        e = self.pi._parse_message('{"type": "input", "event": "prev_device"}')
        assert e.type == EventType.PREV_DEVICE

    def test_quit(self):
        e = self.pi._parse_message('{"type": "input", "event": "quit"}')
        assert e.type == EventType.QUIT

    def test_scan_qr(self):
        e = self.pi._parse_message('{"type": "input", "event": "scan_qr"}')
        assert e.type == EventType.SCAN_QR

    def test_qrlink_valid(self):
        url = "qrlink://v1/monitor-bed-12/mqtt/192.168.1.10:1883?auth=pin&t=ward3/bed12/vitals"
        msg = json.dumps({"type": "qrlink", "url": url})
        e = self.pi._parse_message(msg)
        assert e is not None
        assert e.type == EventType.QRLINK_RECEIVED
        assert e.value == url
        assert e.source == "phone"

    def test_qrlink_minimal(self):
        url = "qrlink://v1/test/mqtt/localhost:1883"
        e = self.pi._parse_message(json.dumps({"type": "qrlink", "url": url}))
        assert e is not None
        assert e.type == EventType.QRLINK_RECEIVED
        assert e.value == url

    def test_qrlink_non_qrlink_url_ignored(self):
        msg = json.dumps({"type": "qrlink", "url": "https://example.com"})
        e = self.pi._parse_message(msg)
        assert e is None

    def test_qrlink_empty_url_ignored(self):
        msg = json.dumps({"type": "qrlink", "url": ""})
        e = self.pi._parse_message(msg)
        assert e is None

    def test_unknown_type_returns_none(self):
        e = self.pi._parse_message('{"type": "unknown", "data": 123}')
        assert e is None

    def test_unknown_event_returns_none(self):
        e = self.pi._parse_message('{"type": "input", "event": "nonexistent"}')
        assert e is None

    def test_invalid_json_returns_none(self):
        e = self.pi._parse_message("not json at all")
        assert e is None

    def test_empty_string_returns_none(self):
        e = self.pi._parse_message("")
        assert e is None

    def test_missing_type_field_returns_none(self):
        e = self.pi._parse_message('{"event": "confirm"}')
        assert e is None

    def test_missing_event_field_returns_none(self):
        e = self.pi._parse_message('{"type": "input"}')
        assert e is None

    def test_none_input_returns_none(self):
        e = self.pi._parse_message(None)
        assert e is None


class TestEventMap:
    """Test that the event map covers all expected inputs."""

    def test_all_nav_events_mapped(self):
        nav = ["nav_up", "nav_down", "nav_left", "nav_right",
               "confirm", "cancel", "home"]
        for name in nav:
            assert name in _EVENT_MAP, f"Missing mapping for {name}"

    def test_all_digit_events_mapped(self):
        digits = ["digit_up", "digit_down", "digit_next",
                   "digit_prev", "digit_submit"]
        for name in digits:
            assert name in _EVENT_MAP, f"Missing mapping for {name}"

    def test_device_events_mapped(self):
        assert "next_device" in _EVENT_MAP
        assert "prev_device" in _EVENT_MAP
        assert "scan_qr" in _EVENT_MAP

    def test_system_events_mapped(self):
        assert "quit" in _EVENT_MAP

    def test_map_values_are_event_types(self):
        for name, etype in _EVENT_MAP.items():
            assert isinstance(etype, EventType), f"{name} maps to non-EventType: {etype}"


class TestQueueBehavior:
    """Test the queue-based event buffering."""

    def setup_method(self):
        self.pi = PhoneInput()

    def test_poll_returns_queued_event(self):
        event = InputEvent(type=EventType.CONFIRM, source="phone")
        self.pi._queue.append(event)
        result = self.pi.poll()
        assert result is not None
        assert result.type == EventType.CONFIRM

    def test_poll_returns_none_when_empty(self):
        assert self.pi.poll() is None

    def test_queue_fifo_order(self):
        e1 = InputEvent(type=EventType.NAV_UP, source="phone")
        e2 = InputEvent(type=EventType.CONFIRM, source="phone")
        self.pi._queue.append(e1)
        self.pi._queue.append(e2)
        assert self.pi.poll().type == EventType.NAV_UP
        assert self.pi.poll().type == EventType.CONFIRM
        assert self.pi.poll() is None

    def test_queue_maxlen_drops_oldest(self):
        for i in range(70):  # maxlen is 64
            self.pi._queue.append(
                InputEvent(type=EventType.NAV_UP, value=i, source="phone")
            )
        assert len(self.pi._queue) == 64
        # Oldest (0-5) should have been dropped
        first = self.pi.poll()
        assert first.value == 6


class TestStateSerialization:
    """Test send_state message format."""

    def test_send_state_basic(self):
        pi = PhoneInput()
        captured = []
        pi._broadcast = lambda msg: captured.append(msg)

        pi.send_state("scanning")
        assert len(captured) == 1
        assert captured[0] == {"type": "state", "state": "scanning"}

    def test_send_state_with_device(self):
        pi = PhoneInput()
        captured = []
        pi._broadcast = lambda msg: captured.append(msg)

        pi.send_state("streaming", device="monitor-bed-12")
        assert captured[0] == {
            "type": "state",
            "state": "streaming",
            "device": "monitor-bed-12",
        }

    def test_send_state_with_error(self):
        pi = PhoneInput()
        captured = []
        pi._broadcast = lambda msg: captured.append(msg)

        pi.send_state("error", error="Connection failed")
        assert captured[0] == {
            "type": "state",
            "state": "error",
            "error": "Connection failed",
        }

    def test_numeric_mode_broadcasts(self):
        pi = PhoneInput()
        captured = []
        pi._broadcast = lambda msg: captured.append(msg)

        pi.numeric_mode = True
        assert len(captured) == 1
        assert captured[0] == {"type": "mode", "numeric": True}

        pi.numeric_mode = False
        assert captured[1] == {"type": "mode", "numeric": False}
