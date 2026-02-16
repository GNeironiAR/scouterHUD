"""Tests for input system (events, backend, manager)."""

import pytest

from scouterhud.input.backend import InputBackend
from scouterhud.input.events import EventType, InputEvent
from scouterhud.input.input_manager import InputManager


class MockBackend(InputBackend):
    """Test backend that returns queued events."""

    def __init__(self, name: str = "mock", events: list[InputEvent] | None = None):
        self._name = name
        self._events = list(events or [])
        self._started = False
        self._available = True
        self.numeric_mode = False

    @property
    def name(self) -> str:
        return self._name

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        self._started = False

    @property
    def is_available(self) -> bool:
        return self._available

    def poll(self) -> InputEvent | None:
        if self._events:
            return self._events.pop(0)
        return None


class TestInputEvent:
    """Tests for InputEvent dataclass."""

    def test_create_event(self):
        e = InputEvent(type=EventType.CONFIRM, source="keyboard")
        assert e.type == EventType.CONFIRM
        assert e.source == "keyboard"
        assert e.value is None
        assert e.timestamp > 0

    def test_event_with_value(self):
        e = InputEvent(type=EventType.DIGIT_UP, value=5, source="gauntlet")
        assert e.value == 5


class TestEventType:
    """Tests for EventType enum."""

    def test_all_event_types_exist(self):
        expected = [
            "NAV_UP", "NAV_DOWN", "NAV_LEFT", "NAV_RIGHT",
            "CONFIRM", "CANCEL", "HOME",
            "DIGIT_UP", "DIGIT_DOWN", "DIGIT_NEXT", "DIGIT_PREV", "DIGIT_SUBMIT",
            "NEXT_DEVICE", "PREV_DEVICE", "SCAN_QR",
            "TOGGLE_VOICE", "LOCK", "QUIT",
        ]
        for name in expected:
            assert hasattr(EventType, name), f"Missing EventType.{name}"

    def test_event_types_are_unique(self):
        values = [e.value for e in EventType]
        assert len(values) == len(set(values))


class TestInputManager:
    """Tests for InputManager."""

    def test_poll_no_backends(self):
        mgr = InputManager()
        assert mgr.poll() is None

    def test_poll_returns_event_from_backend(self):
        event = InputEvent(type=EventType.CONFIRM, source="mock")
        backend = MockBackend(events=[event])
        mgr = InputManager(backends=[backend])
        mgr.start()

        result = mgr.poll()
        assert result is not None
        assert result.type == EventType.CONFIRM

    def test_poll_returns_none_when_empty(self):
        backend = MockBackend(events=[])
        mgr = InputManager(backends=[backend])
        mgr.start()
        assert mgr.poll() is None

    def test_poll_priority_first_backend_wins(self):
        e1 = InputEvent(type=EventType.CONFIRM, source="first")
        e2 = InputEvent(type=EventType.CANCEL, source="second")
        b1 = MockBackend(name="first", events=[e1])
        b2 = MockBackend(name="second", events=[e2])
        mgr = InputManager(backends=[b1, b2])
        mgr.start()

        result = mgr.poll()
        assert result.source == "first"

    def test_poll_skips_unavailable_backend(self):
        e1 = InputEvent(type=EventType.CONFIRM, source="unavail")
        e2 = InputEvent(type=EventType.CANCEL, source="avail")
        b1 = MockBackend(name="unavail", events=[e1])
        b1._available = False
        b2 = MockBackend(name="avail", events=[e2])
        mgr = InputManager(backends=[b1, b2])
        mgr.start()

        result = mgr.poll()
        assert result.source == "avail"

    def test_add_backend(self):
        mgr = InputManager()
        backend = MockBackend()
        mgr.add_backend(backend)

        event = InputEvent(type=EventType.QUIT, source="mock")
        backend._events.append(event)

        assert mgr.poll() is not None

    def test_start_calls_backend_start(self):
        backend = MockBackend()
        mgr = InputManager(backends=[backend])
        mgr.start()
        assert backend._started is True

    def test_stop_calls_backend_stop(self):
        backend = MockBackend()
        mgr = InputManager(backends=[backend])
        mgr.start()
        mgr.stop()
        assert backend._started is False

    def test_set_numeric_mode(self):
        backend = MockBackend()
        mgr = InputManager(backends=[backend])
        mgr.set_numeric_mode(True)
        assert backend.numeric_mode is True
        mgr.set_numeric_mode(False)
        assert backend.numeric_mode is False
