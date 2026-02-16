"""Tests for GauntletInput event translation (no BLE hardware needed)."""

import pytest

from scouterhud.input.gauntlet_input import GauntletInput, PadEvent
from scouterhud.input.events import EventType


class TestGauntletTranslation:
    """Test pad event → InputEvent translation logic."""

    def setup_method(self):
        self.gi = GauntletInput()

    # ── Navigation mode (default) ──

    def test_nav_pad1_left(self):
        e = self.gi._translate_event(PadEvent.TAP, 0b00001)
        assert e is not None
        assert e.type == EventType.NAV_LEFT

    def test_nav_pad2_up(self):
        e = self.gi._translate_event(PadEvent.TAP, 0b00010)
        assert e is not None
        assert e.type == EventType.NAV_UP

    def test_nav_pad3_down(self):
        e = self.gi._translate_event(PadEvent.TAP, 0b00100)
        assert e is not None
        assert e.type == EventType.NAV_DOWN

    def test_nav_pad4_right(self):
        e = self.gi._translate_event(PadEvent.TAP, 0b01000)
        assert e is not None
        assert e.type == EventType.NAV_RIGHT

    def test_nav_pad5_confirm(self):
        e = self.gi._translate_event(PadEvent.TAP, 0b10000)
        assert e is not None
        assert e.type == EventType.CONFIRM

    def test_chord_pad1_pad4_cancel(self):
        e = self.gi._translate_event(PadEvent.CHORD, 0b01001)
        assert e is not None
        assert e.type == EventType.CANCEL

    def test_double_tap_pad5_home(self):
        e = self.gi._translate_event(PadEvent.DOUBLE_TAP, 0b10000)
        assert e is not None
        assert e.type == EventType.HOME

    def test_hold_pad5_toggle_voice(self):
        e = self.gi._translate_event(PadEvent.HOLD, 0b10000)
        assert e is not None
        assert e.type == EventType.TOGGLE_VOICE

    def test_hold_all_pads_lock(self):
        e = self.gi._translate_event(PadEvent.HOLD, 0b11111)
        assert e is not None
        assert e.type == EventType.LOCK

    # ── Numeric mode ──

    def test_numeric_pad1_decrement(self):
        self.gi._numeric_mode = True
        e = self.gi._translate_event(PadEvent.TAP, 0b00001)
        assert e is not None
        assert e.type == EventType.DIGIT_DOWN

    def test_numeric_pad2_prev_digit(self):
        self.gi._numeric_mode = True
        e = self.gi._translate_event(PadEvent.TAP, 0b00010)
        assert e is not None
        assert e.type == EventType.DIGIT_PREV

    def test_numeric_pad3_next_digit(self):
        self.gi._numeric_mode = True
        e = self.gi._translate_event(PadEvent.TAP, 0b00100)
        assert e is not None
        assert e.type == EventType.DIGIT_NEXT

    def test_numeric_pad4_increment(self):
        self.gi._numeric_mode = True
        e = self.gi._translate_event(PadEvent.TAP, 0b01000)
        assert e is not None
        assert e.type == EventType.DIGIT_UP

    def test_numeric_pad5_submit(self):
        self.gi._numeric_mode = True
        e = self.gi._translate_event(PadEvent.TAP, 0b10000)
        assert e is not None
        assert e.type == EventType.DIGIT_SUBMIT

    # ── Edge cases ──

    def test_unknown_pad_returns_none(self):
        e = self.gi._translate_event(PadEvent.TAP, 0b11111)
        assert e is None

    def test_unknown_event_type_returns_none(self):
        e = self.gi._translate_event(0xFF, 0b00001)
        assert e is None

    def test_release_event_ignored(self):
        e = self.gi._translate_event(PadEvent.RELEASE, 0b00001)
        assert e is None

    def test_event_source_is_gauntlet(self):
        e = self.gi._translate_event(PadEvent.TAP, 0b00001)
        assert e.source == "gauntlet"


class TestGauntletNotification:
    """Test the BLE notification parser."""

    def setup_method(self):
        self.gi = GauntletInput()

    def test_parse_4_byte_notification(self):
        # TAP on PAD 2 (NAV_UP), timestamp 0x1234
        data = bytearray([0x01, 0b00010, 0x34, 0x12])
        self.gi._on_input_notification(None, data)

        event = self.gi.poll()
        assert event is not None
        assert event.type == EventType.NAV_UP

    def test_short_data_ignored(self):
        self.gi._on_input_notification(None, bytearray([0x01]))
        assert self.gi.poll() is None

    def test_battery_notification(self):
        self.gi._on_battery_notification(None, bytearray([85]))
        assert self.gi.battery_level == 85


class TestGauntletProperties:
    """Test backend properties."""

    def test_name(self):
        gi = GauntletInput()
        assert gi.name == "gauntlet-ble"

    def test_not_available_without_bleak(self):
        gi = GauntletInput()
        # Not connected, so not available
        assert gi.is_available is False

    def test_numeric_mode_toggle(self):
        gi = GauntletInput()
        assert gi.numeric_mode is False
        gi._numeric_mode = True
        assert gi.numeric_mode is True

    def test_poll_empty(self):
        gi = GauntletInput()
        assert gi.poll() is None
