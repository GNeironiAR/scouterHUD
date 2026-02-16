"""Reusable UI widgets for the 240x240 display.

All widgets draw on a PIL Image with black background.
Black = transparent on the beam splitter, so only colored pixels are visible.
"""

from PIL import Image, ImageDraw, ImageFont

# Colors (bright for visibility through beam splitter)
WHITE = (255, 255, 255)
GREEN = (0, 255, 100)
YELLOW = (255, 220, 0)
RED = (255, 50, 50)
CYAN = (0, 220, 255)
ORANGE = (255, 140, 0)
DIM = (80, 80, 80)
BLACK = (0, 0, 0)


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size
        )
    except OSError:
        return ImageFont.load_default()


# Pre-load common sizes
FONT_LARGE = _get_font(28)
FONT_MEDIUM = _get_font(18)
FONT_SMALL = _get_font(13)
FONT_TINY = _get_font(10)


def value_color(
    value: float,
    schema: dict | None = None,
) -> tuple[int, int, int]:
    """Pick color based on value and schema thresholds."""
    if not schema:
        return WHITE

    alert_above = schema.get("alert_above")
    alert_below = schema.get("alert_below")

    if alert_above is not None and value >= alert_above:
        return RED
    if alert_below is not None and value <= alert_below:
        return RED

    # Warning zone: within 10% of threshold
    if alert_above is not None and value >= alert_above * 0.9:
        return YELLOW
    if alert_below is not None and value <= alert_below * 1.1:
        return YELLOW

    return GREEN


def draw_header(
    draw: ImageDraw.ImageDraw,
    name: str,
    device_type: str,
    y: int = 0,
) -> int:
    """Draw device name header. Returns next y position."""
    # Device name (truncate if too long)
    display_name = name[:22] if len(name) > 22 else name
    draw.text((4, y + 2), display_name, fill=CYAN, font=FONT_SMALL)

    # Type badge
    type_short = device_type.split(".")[-1] if device_type else ""
    draw.text((4, y + 18), type_short, fill=DIM, font=FONT_TINY)

    # Separator line
    draw.line([(0, y + 30), (240, y + 30)], fill=DIM, width=1)

    return y + 34


def draw_big_value(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    value: str,
    unit: str = "",
    color: tuple = GREEN,
    width: int = 110,
) -> None:
    """Draw a large value with label above and unit beside."""
    draw.text((x, y), label, fill=DIM, font=FONT_TINY)
    draw.text((x, y + 12), value, fill=color, font=FONT_LARGE)
    if unit:
        draw.text((x + len(value) * 17 + 4, y + 20), unit, fill=DIM, font=FONT_SMALL)


def draw_small_value(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    value: str,
    unit: str = "",
    color: tuple = WHITE,
) -> None:
    """Draw a compact key-value pair."""
    draw.text((x, y), f"{label}:", fill=DIM, font=FONT_TINY)
    draw.text((x, y + 12), f"{value}{unit}", fill=color, font=FONT_MEDIUM)


def draw_status_bar(
    draw: ImageDraw.ImageDraw,
    y: int,
    status: str,
    alerts: list[str] | None = None,
) -> None:
    """Draw status bar at the bottom of the screen."""
    draw.line([(0, y), (240, y)], fill=DIM, width=1)

    if alerts:
        alert_text = " ".join(alerts)
        draw.rectangle([(0, y + 2), (240, y + 20)], fill=(80, 0, 0))
        draw.text((4, y + 4), f"ALERT: {alert_text}", fill=RED, font=FONT_SMALL)
    else:
        color = GREEN if status in ("stable", "running", "idle") else YELLOW
        draw.text((4, y + 4), status.upper(), fill=color, font=FONT_SMALL)


def draw_alert_flash(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
) -> None:
    """Draw a red border flash for critical alerts."""
    for i in range(3):
        draw.rectangle([(i, i), (width - 1 - i, height - 1 - i)], outline=RED)
