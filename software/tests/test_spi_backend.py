"""Tests for SPIBackend (ST7789 via spidev + gpiozero) — uses mocks, no hardware needed."""

from unittest.mock import MagicMock, patch, call
import sys

import pytest
from PIL import Image


@pytest.fixture(autouse=True)
def mock_hardware():
    """Mock spidev, gpiozero, and numpy so tests run without Pi hardware."""
    # Mock numpy with real functionality we need
    mock_np = MagicMock()

    # We need numpy to actually work for RGB565 conversion,
    # so install it or use a thin mock. Since numpy may not be
    # installed in dev, we mock it but make the show/clear methods
    # work by mocking at a higher level.
    import numpy as np_real
    # numpy IS available — no need to mock it
    np_available = True

    mock_spidev = MagicMock()
    mock_spi_instance = MagicMock()
    mock_spidev.SpiDev.return_value = mock_spi_instance

    mock_gpiozero = MagicMock()
    mock_dc = MagicMock()
    mock_rst = MagicMock()
    mock_bl = MagicMock()
    mock_gpiozero.DigitalOutputDevice.side_effect = [mock_dc, mock_rst]
    mock_gpiozero.PWMOutputDevice.return_value = mock_bl

    sys.modules["spidev"] = mock_spidev
    sys.modules["gpiozero"] = mock_gpiozero

    yield {
        "spidev": mock_spidev,
        "spi": mock_spi_instance,
        "gpiozero": mock_gpiozero,
        "dc": mock_dc,
        "rst": mock_rst,
        "bl": mock_bl,
    }

    del sys.modules["spidev"]
    del sys.modules["gpiozero"]


def _make_backend(mock_hw, **kwargs):
    """Create SPIBackend with fresh mocks."""
    mock_dc = MagicMock()
    mock_rst = MagicMock()
    mock_bl = MagicMock()
    mock_hw["gpiozero"].DigitalOutputDevice.side_effect = [mock_dc, mock_rst]
    mock_hw["gpiozero"].PWMOutputDevice.return_value = mock_bl
    mock_hw["dc"] = mock_dc
    mock_hw["rst"] = mock_rst
    mock_hw["bl"] = mock_bl

    mock_spi = MagicMock()
    mock_hw["spidev"].SpiDev.return_value = mock_spi
    mock_hw["spi"] = mock_spi

    if "scouterhud.display.backend_spi" in sys.modules:
        del sys.modules["scouterhud.display.backend_spi"]
    from scouterhud.display.backend_spi import SPIBackend

    return SPIBackend(**kwargs)


class TestSPIBackendInit:

    def test_default_pins(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        hw = mock_hardware

        hw["gpiozero"].DigitalOutputDevice.assert_any_call(
            25, active_high=True, initial_value=False
        )
        hw["gpiozero"].DigitalOutputDevice.assert_any_call(
            27, active_high=True, initial_value=False
        )
        hw["gpiozero"].PWMOutputDevice.assert_called_once_with(24, frequency=1000)
        hw["spi"].open.assert_called_once_with(0, 0)
        assert hw["spi"].max_speed_hz == 8_000_000
        assert hw["spi"].mode == 0b00

    def test_custom_pins(self, mock_hardware):
        backend = _make_backend(
            mock_hardware,
            dc_pin=17, rst_pin=22, backlight_pin=18,
            spi_speed_hz=40_000_000, spi_port=1, spi_cs=1,
        )
        hw = mock_hardware

        hw["gpiozero"].DigitalOutputDevice.assert_any_call(
            17, active_high=True, initial_value=False
        )
        hw["gpiozero"].DigitalOutputDevice.assert_any_call(
            22, active_high=True, initial_value=False
        )
        hw["gpiozero"].PWMOutputDevice.assert_called_once_with(18, frequency=1000)
        hw["spi"].open.assert_called_once_with(1, 1)
        assert hw["spi"].max_speed_hz == 40_000_000

    def test_default_backlight_90_percent(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        assert mock_hardware["bl"].value == 0.9

    def test_init_sends_sleep_out_and_display_on(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]

        commands_sent = []
        for c in spi.writebytes.call_args_list:
            data = c[0][0]
            if isinstance(data, list):
                commands_sent.extend(data)
            else:
                commands_sent.append(data)

        assert 0x11 in commands_sent  # Sleep out
        assert 0x29 in commands_sent  # Display on
        assert 0x36 in commands_sent  # MADCTL (rotation)
        assert 0x3A in commands_sent  # Color mode
        assert 0x21 in commands_sent  # Inversion on


class TestSPIBackendRotation:

    def test_rotation_0_no_offset(self, mock_hardware):
        backend = _make_backend(mock_hardware, rotation=0)
        assert backend._madctl == 0x00
        assert backend._x_offset == 0
        assert backend._y_offset == 0

    def test_rotation_1_90_degrees(self, mock_hardware):
        backend = _make_backend(mock_hardware, rotation=1)
        assert backend._madctl == 0x60
        assert backend._x_offset == 0
        assert backend._y_offset == 0

    def test_rotation_2_180_degrees_y_offset(self, mock_hardware):
        backend = _make_backend(mock_hardware, rotation=2)
        assert backend._madctl == 0xC0
        assert backend._x_offset == 0
        assert backend._y_offset == 80

    def test_rotation_3_270_degrees_x_offset(self, mock_hardware):
        backend = _make_backend(mock_hardware, rotation=3)
        assert backend._madctl == 0xA0
        assert backend._x_offset == 80
        assert backend._y_offset == 0

    def test_invalid_rotation_defaults_to_0(self, mock_hardware):
        backend = _make_backend(mock_hardware, rotation=5)
        assert backend._madctl == 0x00
        assert backend._x_offset == 0
        assert backend._y_offset == 0


class TestSPIBackendShow:

    def test_show_sends_pixel_data_via_spi(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        spi.writebytes.reset_mock()

        img = Image.new("RGB", (240, 240), (255, 0, 0))
        backend.show(img)

        assert spi.writebytes.call_count > 0

    def test_show_sends_correct_pixel_count(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        spi.writebytes.reset_mock()

        img = Image.new("RGB", (240, 240), (255, 0, 0))
        backend.show(img)

        # 240*240*2 = 115200 bytes (RGB565), sent in 4096-byte chunks
        total_pixel_bytes = 240 * 240 * 2
        all_writes = spi.writebytes.call_args_list
        pixel_bytes_sent = sum(
            len(c[0][0]) for c in all_writes if len(c[0][0]) > 100
        )
        assert pixel_bytes_sent == total_pixel_bytes

    def test_show_resizes_if_needed(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        spi.writebytes.reset_mock()

        img = Image.new("RGB", (480, 480), (0, 255, 0))
        backend.show(img)

        all_writes = spi.writebytes.call_args_list
        pixel_bytes_sent = sum(
            len(c[0][0]) for c in all_writes if len(c[0][0]) > 100
        )
        assert pixel_bytes_sent == 240 * 240 * 2

    def test_show_converts_rgba_to_rgb(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        spi.writebytes.reset_mock()

        img = Image.new("RGBA", (240, 240), (0, 0, 255, 128))
        backend.show(img)

        assert spi.writebytes.call_count > 0

    def test_show_rgb565_red_encoding(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        spi.writebytes.reset_mock()

        # Pure red (255, 0, 0) -> RGB565: high=0xF8, low=0x00
        img = Image.new("RGB", (240, 240), (255, 0, 0))
        backend.show(img)

        pixel_data = []
        for c in spi.writebytes.call_args_list:
            if len(c[0][0]) > 100:
                pixel_data.extend(c[0][0])

        assert pixel_data[0] == 0xF8
        assert pixel_data[1] == 0x00

    def test_show_rgb565_green_encoding(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        spi.writebytes.reset_mock()

        # Pure green (0, 255, 0) -> RGB565: high=0x07, low=0xE0
        img = Image.new("RGB", (240, 240), (0, 255, 0))
        backend.show(img)

        pixel_data = []
        for c in spi.writebytes.call_args_list:
            if len(c[0][0]) > 100:
                pixel_data.extend(c[0][0])

        assert pixel_data[0] == 0x07
        assert pixel_data[1] == 0xE0

    def test_show_rgb565_blue_encoding(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        spi.writebytes.reset_mock()

        # Pure blue (0, 0, 255) -> RGB565: high=0x00, low=0x1F
        img = Image.new("RGB", (240, 240), (0, 0, 255))
        backend.show(img)

        pixel_data = []
        for c in spi.writebytes.call_args_list:
            if len(c[0][0]) > 100:
                pixel_data.extend(c[0][0])

        assert pixel_data[0] == 0x00
        assert pixel_data[1] == 0x1F


class TestSPIBackendClear:

    def test_clear_sends_black_pixels(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        spi.writebytes.reset_mock()

        backend.clear()

        all_writes = spi.writebytes.call_args_list
        pixel_data = []
        for c in all_writes:
            if len(c[0][0]) > 100:
                pixel_data.extend(c[0][0])

        assert len(pixel_data) == 240 * 240 * 2
        assert all(b == 0 for b in pixel_data)


class TestSPIBackendClose:

    def test_close_clears_and_turns_off_backlight(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        spi = mock_hardware["spi"]
        bl = mock_hardware["bl"]
        spi.writebytes.reset_mock()

        backend.close()

        assert spi.writebytes.call_count > 0
        assert bl.value == 0
        spi.close.assert_called_once()


class TestSPIBackendBrightness:

    def test_set_brightness_updates_pwm(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        bl = mock_hardware["bl"]

        backend.set_brightness(128)
        assert backend._brightness == 128
        assert abs(bl.value - 128 / 255.0) < 0.01

    def test_set_brightness_clamps_to_range(self, mock_hardware):
        backend = _make_backend(mock_hardware)

        backend.set_brightness(0)
        assert backend._brightness == 0

        backend.set_brightness(255)
        assert backend._brightness == 255

        backend.set_brightness(-10)
        assert backend._brightness == 0

        backend.set_brightness(999)
        assert backend._brightness == 255


class TestSPIBackendProperties:

    def test_width_and_height(self, mock_hardware):
        backend = _make_backend(mock_hardware)
        assert backend.width == 240
        assert backend.height == 240
