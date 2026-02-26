"""Tests for SPIBackend (ST7789 display) — uses mocks, no hardware needed."""

from unittest.mock import MagicMock, patch
import sys

import pytest
from PIL import Image


@pytest.fixture(autouse=True)
def mock_st7789():
    """Mock the st7789 module so tests run without Pi hardware."""
    mock_module = MagicMock()
    mock_display = MagicMock()
    mock_module.ST7789.return_value = mock_display
    sys.modules["st7789"] = mock_module
    yield mock_module, mock_display
    del sys.modules["st7789"]


def _make_backend(**kwargs):
    from scouterhud.display.backend_spi import SPIBackend
    return SPIBackend(**kwargs)


class TestSPIBackendInit:

    def test_default_pins(self, mock_st7789):
        mock_module, mock_display = mock_st7789
        backend = _make_backend()

        mock_module.ST7789.assert_called_once_with(
            height=240, width=240, rotation=0,
            port=0, cs=0, dc=25, rst=24, backlight=18,
            spi_speed_hz=40_000_000,
        )
        mock_display.begin.assert_called_once()

    def test_custom_pins(self, mock_st7789):
        mock_module, mock_display = mock_st7789
        backend = _make_backend(
            dc_pin=17, rst_pin=27, backlight_pin=22,
            spi_speed_hz=20_000_000, rotation=2,
            spi_port=1, spi_cs=1,
        )

        mock_module.ST7789.assert_called_once_with(
            height=240, width=240, rotation=2,
            port=1, cs=1, dc=17, rst=27, backlight=22,
            spi_speed_hz=20_000_000,
        )


class TestSPIBackendShow:

    def test_show_sends_image_to_display(self, mock_st7789):
        _, mock_display = mock_st7789
        backend = _make_backend()
        img = Image.new("RGB", (240, 240), (255, 0, 0))

        backend.show(img)

        mock_display.display.assert_called_once()
        sent_img = mock_display.display.call_args[0][0]
        assert sent_img.size == (240, 240)
        assert sent_img.mode == "RGB"

    def test_show_resizes_if_needed(self, mock_st7789):
        _, mock_display = mock_st7789
        backend = _make_backend()
        img = Image.new("RGB", (480, 480), (0, 255, 0))

        backend.show(img)

        sent_img = mock_display.display.call_args[0][0]
        assert sent_img.size == (240, 240)

    def test_show_converts_rgba_to_rgb(self, mock_st7789):
        _, mock_display = mock_st7789
        backend = _make_backend()
        img = Image.new("RGBA", (240, 240), (0, 0, 255, 128))

        backend.show(img)

        sent_img = mock_display.display.call_args[0][0]
        assert sent_img.mode == "RGB"


class TestSPIBackendClear:

    def test_clear_sends_black_image(self, mock_st7789):
        _, mock_display = mock_st7789
        backend = _make_backend()
        mock_display.display.reset_mock()

        backend.clear()

        mock_display.display.assert_called_once()
        sent_img = mock_display.display.call_args[0][0]
        assert sent_img.size == (240, 240)
        # Verify all black
        pixels = list(sent_img.tobytes())
        assert all(b == 0 for b in pixels)


class TestSPIBackendClose:

    def test_close_clears_display(self, mock_st7789):
        _, mock_display = mock_st7789
        backend = _make_backend()
        mock_display.display.reset_mock()

        backend.close()

        # close() should call clear() which sends a black image
        mock_display.display.assert_called_once()


class TestSPIBackendBrightness:

    def test_set_brightness_clamps_to_range(self, mock_st7789):
        backend = _make_backend()

        backend.set_brightness(128)
        assert backend._brightness == 128

        backend.set_brightness(0)
        assert backend._brightness == 0

        backend.set_brightness(255)
        assert backend._brightness == 255

        backend.set_brightness(-10)
        assert backend._brightness == 0

        backend.set_brightness(999)
        assert backend._brightness == 255


class TestSPIBackendProperties:

    def test_width_and_height(self, mock_st7789):
        backend = _make_backend()
        assert backend.width == 240
        assert backend.height == 240
