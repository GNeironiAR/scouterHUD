"""Tests for ConnectionManager (device history and switching logic).

Note: These tests mock the MQTT transport to avoid needing a real broker.
"""

import pytest
from unittest.mock import patch, MagicMock

from scouterhud.qrlink.connection import ConnectionManager
from scouterhud.qrlink.protocol import DeviceLink


def _make_link(device_id: str = "dev-1", **kwargs):
    defaults = dict(version=1, id=device_id, proto="mqtt", host="localhost", port=1883)
    defaults.update(kwargs)
    return DeviceLink(**defaults)


def _noop_data(data):
    pass


class TestDeviceHistory:
    """Tests for device history management (no MQTT needed)."""

    def test_initial_state(self):
        cm = ConnectionManager()
        assert cm.active_device is None
        assert cm.is_connected is False
        assert cm.known_devices == []
        assert cm.device_count == 0

    @patch("scouterhud.qrlink.connection.MQTTTransport")
    def test_connect_adds_to_history(self, MockTransport):
        mock = MockTransport.return_value
        mock.connect.return_value = True

        cm = ConnectionManager()
        link = _make_link("dev-1")
        cm.connect(link, on_data=_noop_data)

        assert cm.device_count == 1
        assert cm.known_devices[0].id == "dev-1"

    @patch("scouterhud.qrlink.connection.MQTTTransport")
    def test_connect_multiple_devices(self, MockTransport):
        mock = MockTransport.return_value
        mock.connect.return_value = True

        cm = ConnectionManager()
        cm.connect(_make_link("dev-1"), on_data=_noop_data)
        cm.connect(_make_link("dev-2"), on_data=_noop_data)
        cm.connect(_make_link("dev-3"), on_data=_noop_data)

        assert cm.device_count == 3
        ids = [d.id for d in cm.known_devices]
        assert ids == ["dev-1", "dev-2", "dev-3"]

    @patch("scouterhud.qrlink.connection.MQTTTransport")
    def test_connect_deduplicates_by_id(self, MockTransport):
        mock = MockTransport.return_value
        mock.connect.return_value = True

        cm = ConnectionManager()
        cm.connect(_make_link("dev-1"), on_data=_noop_data)
        cm.connect(_make_link("dev-2"), on_data=_noop_data)
        cm.connect(_make_link("dev-1"), on_data=_noop_data)  # reconnect

        assert cm.device_count == 2
        # dev-1 should be at the end (most recent)
        assert cm.known_devices[-1].id == "dev-1"

    @patch("scouterhud.qrlink.connection.MQTTTransport")
    def test_active_device_tracks_current(self, MockTransport):
        mock = MockTransport.return_value
        mock.connect.return_value = True

        cm = ConnectionManager()
        link = _make_link("dev-1")
        cm.connect(link, on_data=_noop_data)

        assert cm.active_device is not None
        assert cm.active_device.id == "dev-1"

    @patch("scouterhud.qrlink.connection.MQTTTransport")
    def test_connect_failure(self, MockTransport):
        mock = MockTransport.return_value
        mock.connect.return_value = False

        cm = ConnectionManager()
        result = cm.connect(_make_link("dev-1"), on_data=_noop_data)

        assert result is False
        assert cm.active_device is None
        assert cm.device_count == 0


class TestDeviceSwitching:
    """Tests for next/prev device switching."""

    def test_switch_next_single_device(self):
        cm = ConnectionManager()
        cm._known_devices = [_make_link("dev-1")]
        cm._active_index = 0

        assert cm.switch_next() is None

    def test_switch_prev_single_device(self):
        cm = ConnectionManager()
        cm._known_devices = [_make_link("dev-1")]
        cm._active_index = 0

        assert cm.switch_prev() is None

    def test_switch_next_cycles(self):
        cm = ConnectionManager()
        cm._known_devices = [_make_link("a"), _make_link("b"), _make_link("c")]
        cm._active_index = 0

        link = cm.switch_next()
        assert link.id == "b"
        link = cm.switch_next()
        assert link.id == "c"
        link = cm.switch_next()
        assert link.id == "a"  # wraps around

    def test_switch_prev_cycles(self):
        cm = ConnectionManager()
        cm._known_devices = [_make_link("a"), _make_link("b"), _make_link("c")]
        cm._active_index = 0

        link = cm.switch_prev()
        assert link.id == "c"  # wraps to end
        link = cm.switch_prev()
        assert link.id == "b"

    def test_switch_empty_list(self):
        cm = ConnectionManager()
        assert cm.switch_next() is None
        assert cm.switch_prev() is None

    @patch("scouterhud.qrlink.connection.MQTTTransport")
    def test_disconnect_clears_active(self, MockTransport):
        mock = MockTransport.return_value
        mock.connect.return_value = True

        cm = ConnectionManager()
        cm.connect(_make_link("dev-1"), on_data=_noop_data)
        cm.disconnect()

        assert cm.active_device is None
        # History is preserved
        assert cm.device_count == 1
