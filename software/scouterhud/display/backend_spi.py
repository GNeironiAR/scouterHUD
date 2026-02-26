"""SPI display backend for ST7789 240x240 on Raspberry Pi.

Requires hardware: Raspberry Pi with SPI enabled + ST7789 display.
Install deps: pip install -e ".[pi]"  (st7789, RPi.GPIO, spidev)

Default wiring (Pi Zero 2W → ST7789 7-pin):
    GND  → Pin 6  (GND)
    VCC  → Pin 1  (3.3V)
    SCL  → Pin 23 (GPIO 11 — SPI0 SCLK)
    SDA  → Pin 19 (GPIO 10 — SPI0 MOSI)
    CS   → Pin 24 (GPIO 8  — SPI0 CE0)
    DC   → Pin 22 (GPIO 25)
    RST  → Pin 18 (GPIO 24)
    BL   → Pin 12 (GPIO 18 — PWM) or 3.3V direct
"""

from PIL import Image

from scouterhud.display.backend import DISPLAY_HEIGHT, DISPLAY_WIDTH, DisplayBackend


class SPIBackend(DisplayBackend):
    """ST7789 SPI display backend for Raspberry Pi."""

    def __init__(
        self,
        dc_pin: int = 25,
        rst_pin: int = 24,
        backlight_pin: int = 18,
        spi_speed_hz: int = 40_000_000,
        rotation: int = 0,
        spi_port: int = 0,
        spi_cs: int = 0,
    ):
        import st7789  # Conditional import — only available on Pi

        self._st7789 = st7789
        self._display = st7789.ST7789(
            height=DISPLAY_HEIGHT,
            width=DISPLAY_WIDTH,
            rotation=rotation,
            port=spi_port,
            cs=spi_cs,
            dc=dc_pin,
            rst=rst_pin,
            backlight=backlight_pin,
            spi_speed_hz=spi_speed_hz,
        )
        self._display.begin()
        self._brightness = 255

    def show(self, image: Image.Image) -> None:
        """Send a PIL Image to the ST7789 display via SPI."""
        img = image.convert("RGB")
        if img.size != (DISPLAY_WIDTH, DISPLAY_HEIGHT):
            img = img.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT), Image.NEAREST)
        self._display.display(img)

    def set_brightness(self, level: int) -> None:
        """Set backlight brightness (0-255). Requires PWM-capable backlight pin."""
        self._brightness = max(0, min(255, level))

    def clear(self) -> None:
        """Clear display to black."""
        black = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0))
        self._display.display(black)

    def close(self) -> None:
        """Clear display and release resources."""
        self.clear()
