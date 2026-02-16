"""Tests for display renderer."""

import pytest
from PIL import Image

from scouterhud.display.renderer import (
    render_connecting_screen,
    render_device_list,
    render_error_screen,
    render_frame,
    render_scanning_screen,
)
from scouterhud.qrlink.protocol import DeviceLink


def _make_link(**kwargs):
    defaults = dict(version=1, id="test-01", proto="mqtt", host="localhost", port=1883)
    defaults.update(kwargs)
    return DeviceLink(**defaults)


def _assert_valid_frame(img: Image.Image):
    """Assert image is a valid 240x240 RGB frame."""
    assert isinstance(img, Image.Image)
    assert img.size == (240, 240)
    assert img.mode == "RGB"


class TestStatusScreens:
    """Tests for static status screens."""

    def test_scanning_screen(self):
        _assert_valid_frame(render_scanning_screen())

    def test_connecting_screen(self):
        _assert_valid_frame(render_connecting_screen("monitor-bed-12"))

    def test_connecting_screen_long_id(self):
        _assert_valid_frame(render_connecting_screen("a" * 100))

    def test_error_screen(self):
        _assert_valid_frame(render_error_screen("Something went wrong"))

    def test_error_screen_long_message(self):
        msg = "This is a very long error message that should be word-wrapped across multiple lines on the display"
        _assert_valid_frame(render_error_screen(msg))

    def test_error_screen_empty_message(self):
        _assert_valid_frame(render_error_screen(""))


class TestDeviceList:
    """Tests for device list screen."""

    def test_empty_device_list(self):
        _assert_valid_frame(render_device_list([], 0, ""))

    def test_single_device(self):
        devices = [_make_link(id="dev-1", name="Device 1", type="medical.monitor")]
        _assert_valid_frame(render_device_list(devices, 0, "dev-1"))

    def test_multiple_devices(self):
        devices = [
            _make_link(id=f"dev-{i}", name=f"Device {i}", type="medical.monitor")
            for i in range(8)
        ]
        _assert_valid_frame(render_device_list(devices, 3, "dev-0"))

    def test_device_with_pin_badge(self):
        devices = [_make_link(id="dev-1", auth="pin")]
        _assert_valid_frame(render_device_list(devices, 0, ""))


class TestRenderFrame:
    """Tests for render_frame with different device types."""

    def test_medical_layout(self):
        link = _make_link(
            name="Bed 12",
            type="medical.patient_monitor",
            schema={"spo2": {"alert_below": 90}, "heart_rate": {"alert_above": 120}},
        )
        data = {
            "spo2": 97,
            "heart_rate": 72,
            "resp_rate": 16,
            "temp_c": 36.8,
            "status": "stable",
            "alerts": [],
        }
        _assert_valid_frame(render_frame(link, data))

    def test_medical_with_alerts(self):
        link = _make_link(name="Bed 12", type="medical.patient_monitor")
        data = {
            "spo2": 85,
            "heart_rate": 130,
            "resp_rate": 22,
            "temp_c": 39.1,
            "status": "critical",
            "alerts": ["SpO2 LOW", "HR HIGH"],
        }
        img = render_frame(link, data)
        _assert_valid_frame(img)
        # Alert border should make edge pixels red
        assert img.getpixel((0, 0)) == (255, 50, 50)

    def test_vehicle_layout(self):
        link = _make_link(name="Car 001", type="vehicle.obd2")
        data = {
            "rpm": 2400,
            "speed_kmh": 65,
            "coolant_temp_c": 90,
            "fuel_pct": 72,
            "battery_v": 12.6,
            "dtc_codes": [],
        }
        _assert_valid_frame(render_frame(link, data))

    def test_infra_layout(self):
        link = _make_link(name="srv-prod-01", type="infra.server")
        data = {
            "cpu_pct": 45,
            "mem_pct": 68,
            "disk_pct": 55,
            "monthly_cost_usd": 142.5,
            "active_alerts": 0,
            "instance_id": "i-abc123",
        }
        _assert_valid_frame(render_frame(link, data))

    def test_home_layout(self):
        link = _make_link(name="Kitchen", type="home.thermostat")
        data = {
            "temp_c": 22.5,
            "target_temp_c": 23.0,
            "humidity_pct": 45,
            "mode": "heating",
        }
        _assert_valid_frame(render_frame(link, data))

    def test_industrial_layout(self):
        link = _make_link(name="Press 07", type="industrial.press")
        data = {
            "pressure_bar": 185,
            "temp_c": 62,
            "cycle_count": 15420,
            "status": "running",
        }
        _assert_valid_frame(render_frame(link, data))

    def test_generic_layout_unknown_type(self):
        link = _make_link(name="Unknown", type="custom.thing")
        data = {"key1": "value1", "key2": 42, "ts": 1234567890}
        _assert_valid_frame(render_frame(link, data))

    def test_generic_layout_no_type(self):
        link = _make_link(name="No Type")
        data = {"temp": 25, "humidity": 60}
        _assert_valid_frame(render_frame(link, data))

    def test_missing_data_fields_use_dashes(self):
        link = _make_link(name="Bed 12", type="medical.patient_monitor")
        data = {}  # no fields at all
        _assert_valid_frame(render_frame(link, data))
