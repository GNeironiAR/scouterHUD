"""SPI display backend for ST7789 240x240 on Raspberry Pi.

Requires hardware: Raspberry Pi with SPI enabled + ST7789 display.
Uses spidev + gpiozero directly (Seengreat driver approach).

Default wiring (Pi Zero 2W → Seengreat ST7789 8-pin JST):
    VCC  → Pin 1  (3.3V)
    GND  → Pin 6  (GND)
    DIN  → Pin 19 (GPIO 10 — SPI0 MOSI)
    CLK  → Pin 23 (GPIO 11 — SPI0 SCLK)
    RST  → Pin 13 (GPIO 27)
    DC   → Pin 22 (GPIO 25)
    CS   → Pin 24 (GPIO 8  — SPI0 CE0)
    BL   → Pin 18 (GPIO 24 — PWM)
"""

import time

import numpy as np
import spidev
from gpiozero import DigitalOutputDevice, PWMOutputDevice
from PIL import Image

from scouterhud.display.backend import DISPLAY_HEIGHT, DISPLAY_WIDTH, DisplayBackend


class SPIBackend(DisplayBackend):
    """ST7789 SPI display backend using spidev + gpiozero (Seengreat compatible)."""

    def __init__(
        self,
        dc_pin: int = 25,
        rst_pin: int = 27,
        backlight_pin: int = 24,
        spi_speed_hz: int = 8_000_000,
        rotation: int = 0,
        spi_port: int = 0,
        spi_cs: int = 0,
    ):
        self._dc = DigitalOutputDevice(dc_pin, active_high=True, initial_value=False)
        self._rst = DigitalOutputDevice(rst_pin, active_high=True, initial_value=False)
        self._bl = PWMOutputDevice(backlight_pin, frequency=1000)
        self._bl.value = 0.9

        self._spi = spidev.SpiDev()
        self._spi.open(spi_port, spi_cs)
        self._spi.max_speed_hz = spi_speed_hz
        self._spi.mode = 0b00

        self._w = DISPLAY_WIDTH
        self._h = DISPLAY_HEIGHT
        self._rotation = rotation
        self._brightness = 255

        # MADCTL values and memory offsets for ST7789 240x240 rotation
        # ST7789 has 320x240 internal RAM; 240x240 displays need offsets
        self._rotation_config = {
            0: (0x00, 0, 0),    # 0°   — normal
            1: (0x60, 0, 0),    # 90°  — MV + MX
            2: (0xC0, 0, 80),   # 180° — MY + MX, Y offset 80 (320-240)
            3: (0xA0, 80, 0),   # 270° — MV + MY, X offset 80
        }
        cfg = self._rotation_config.get(rotation, (0x00, 0, 0))
        self._madctl = cfg[0]
        self._x_offset = cfg[1]
        self._y_offset = cfg[2]

        self._init_display()

    def _write_cmd(self, cmd: int) -> None:
        self._dc.off()
        self._spi.writebytes([cmd])

    def _write_data(self, value: int) -> None:
        self._dc.on()
        self._spi.writebytes([value])

    def _reset(self) -> None:
        self._rst.on()
        time.sleep(0.01)
        self._rst.off()
        time.sleep(0.01)
        self._rst.on()
        time.sleep(0.01)

    def _init_display(self) -> None:
        self._reset()

        self._write_cmd(0x11)  # Sleep out
        time.sleep(0.12)

        self._write_cmd(0x36)  # Memory access control (rotation)
        self._write_data(self._madctl)

        self._write_cmd(0x3A)  # Color mode: 16-bit
        self._write_data(0x05)

        self._write_cmd(0xB2)  # Porch setting
        for v in [0x0C, 0x0C, 0x00, 0x33, 0x33]:
            self._write_data(v)

        self._write_cmd(0xB7)  # Gate control
        self._write_data(0x35)

        self._write_cmd(0xBB)  # VCOM setting
        self._write_data(0x37)

        self._write_cmd(0xC0)  # LCM control
        self._write_data(0x2C)

        self._write_cmd(0xC2)  # VDV/VRH enable
        self._write_data(0x01)

        self._write_cmd(0xC3)  # VRH set
        self._write_data(0x12)

        self._write_cmd(0xC4)  # VDV set
        self._write_data(0x20)

        self._write_cmd(0xC6)  # Frame rate: 60Hz
        self._write_data(0x0F)

        self._write_cmd(0xD0)  # Power control
        self._write_data(0xA4)
        self._write_data(0xA1)

        self._write_cmd(0xE0)  # Positive gamma
        for v in [0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23]:
            self._write_data(v)

        self._write_cmd(0xE1)  # Negative gamma
        for v in [0xD4, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23]:
            self._write_data(v)

        self._write_cmd(0x21)  # Inversion on
        time.sleep(0.12)
        self._write_cmd(0x29)  # Display on
        time.sleep(0.05)

    def _set_window(self, x0: int, y0: int, x1: int, y1: int) -> None:
        x0 += self._x_offset
        x1 += self._x_offset - 1
        y0 += self._y_offset
        y1 += self._y_offset - 1
        self._write_cmd(0x2A)
        self._write_data(x0 >> 8)
        self._write_data(x0 & 0xFF)
        self._write_data(x1 >> 8)
        self._write_data(x1 & 0xFF)

        self._write_cmd(0x2B)
        self._write_data(y0 >> 8)
        self._write_data(y0 & 0xFF)
        self._write_data(y1 >> 8)
        self._write_data(y1 & 0xFF)

        self._write_cmd(0x2C)

    def show(self, image: Image.Image) -> None:
        """Send a PIL Image to the ST7789 display via SPI."""
        img = image.convert("RGB")
        if img.size != (self._w, self._h):
            img = img.resize((self._w, self._h), Image.NEAREST)
        # Rotation handled by hardware MADCTL register, no software rotate needed

        arr = np.asarray(img)
        pixel = np.zeros((self._h, self._w, 2), dtype=np.uint8)
        pixel[..., [0]] = np.add(
            np.bitwise_and(arr[..., [0]], 0xF8),
            np.right_shift(arr[..., [1]], 5),
        )
        pixel[..., [1]] = np.add(
            np.bitwise_and(np.left_shift(arr[..., [1]], 3), 0xE0),
            np.right_shift(arr[..., [2]], 3),
        )
        pixel = pixel.flatten().tolist()

        self._set_window(0, 0, self._w, self._h)
        self._dc.on()
        for i in range(0, len(pixel), 4096):
            self._spi.writebytes(pixel[i : i + 4096])

    def set_brightness(self, level: int) -> None:
        """Set backlight brightness (0-255)."""
        self._brightness = max(0, min(255, level))
        self._bl.value = self._brightness / 255.0

    def clear(self) -> None:
        """Clear display to black."""
        self._set_window(0, 0, self._w, self._h)
        self._dc.on()
        buf = [0x00] * (self._w * self._h * 2)
        for i in range(0, len(buf), 4096):
            self._spi.writebytes(buf[i : i + 4096])

    def close(self) -> None:
        """Clear display and release resources."""
        self.clear()
        self._bl.value = 0
        self._spi.close()
