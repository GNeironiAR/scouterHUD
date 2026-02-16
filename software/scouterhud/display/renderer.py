"""Layout engine for rendering device data on the 240x240 display.

Selects layout based on device type and renders data into a PIL Image
ready to be sent to the display backend.
"""

from typing import Any

from PIL import Image, ImageDraw

from scouterhud.display.backend import DISPLAY_WIDTH, DISPLAY_HEIGHT
from scouterhud.display.widgets import (
    BLACK, CYAN, DIM, GREEN, ORANGE, RED, WHITE, YELLOW,
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_TINY,
    draw_alert_flash,
    draw_big_value,
    draw_header,
    draw_small_value,
    draw_status_bar,
    value_color,
)
from scouterhud.qrlink.protocol import DeviceLink


def render_frame(link: DeviceLink, data: dict[str, Any]) -> Image.Image:
    """Render a data frame for the given device. Returns a 240x240 PIL Image."""
    img = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), BLACK)
    draw = ImageDraw.Draw(img)

    device_type = link.type or ""

    if device_type.startswith("medical."):
        _render_medical(draw, link, data)
    elif device_type.startswith("vehicle."):
        _render_vehicle(draw, link, data)
    elif device_type.startswith("infra."):
        _render_infra(draw, link, data)
    elif device_type.startswith("home."):
        _render_home(draw, link, data)
    elif device_type.startswith("industrial."):
        _render_industrial(draw, link, data)
    else:
        _render_generic(draw, link, data)

    # Alert flash border
    alerts = data.get("alerts", [])
    if alerts:
        draw_alert_flash(draw, DISPLAY_WIDTH, DISPLAY_HEIGHT)

    return img


def _render_medical(draw: ImageDraw.ImageDraw, link: DeviceLink, data: dict) -> None:
    """Medical layout: large vitals with color coding."""
    schema = link.schema
    y = draw_header(draw, link.name or link.id, link.type or "", y=0)

    # SpO2 — big, left
    spo2 = data.get("spo2", "--")
    spo2_color = value_color(spo2, schema.get("spo2")) if isinstance(spo2, (int, float)) else WHITE
    draw_big_value(draw, 4, y, "SpO2", str(spo2), "%", spo2_color)

    # Heart Rate — big, right
    hr = data.get("heart_rate", "--")
    hr_color = value_color(hr, schema.get("heart_rate")) if isinstance(hr, (int, float)) else WHITE
    draw_big_value(draw, 124, y, "HR", str(hr), "bpm", hr_color)

    y += 55

    # Resp Rate — small, left
    rr = data.get("resp_rate", "--")
    draw_small_value(draw, 4, y, "Resp", str(rr), " rpm", WHITE)

    # Temp — small, right
    temp = data.get("temp_c", "--")
    draw_small_value(draw, 124, y, "Temp", str(temp), "\u00b0C", WHITE)

    # Status / alerts at bottom
    status = data.get("status", "unknown")
    alerts = data.get("alerts", [])
    draw_status_bar(draw, 215, status, alerts)


def _render_vehicle(draw: ImageDraw.ImageDraw, link: DeviceLink, data: dict) -> None:
    """Vehicle layout: RPM + speed prominently, gauges below."""
    schema = link.schema
    y = draw_header(draw, link.name or link.id, link.type or "", y=0)

    # RPM — big, left
    rpm = data.get("rpm", "--")
    rpm_color = value_color(rpm, schema.get("rpm")) if isinstance(rpm, (int, float)) else WHITE
    draw_big_value(draw, 4, y, "RPM", str(rpm), "", rpm_color)

    # Speed — big, right
    speed = data.get("speed_kmh", "--")
    draw_big_value(draw, 124, y, "km/h", str(speed), "", CYAN)

    y += 55

    # Coolant temp
    coolant = data.get("coolant_temp_c", "--")
    coolant_color = value_color(coolant, schema.get("coolant_temp_c")) if isinstance(coolant, (int, float)) else WHITE
    draw_small_value(draw, 4, y, "Coolant", str(coolant), "\u00b0C", coolant_color)

    # Fuel
    fuel = data.get("fuel_pct", "--")
    fuel_color = value_color(fuel, schema.get("fuel_pct")) if isinstance(fuel, (int, float)) else WHITE
    draw_small_value(draw, 124, y, "Fuel", str(fuel), "%", fuel_color)

    y += 40

    # Battery
    batt = data.get("battery_v", "--")
    draw_small_value(draw, 4, y, "Battery", str(batt), "V", WHITE)

    # DTC codes
    dtc = data.get("dtc_codes", [])
    if dtc:
        draw.text((124, y + 2), "DTC:", fill=DIM, font=FONT_TINY)
        draw.text((124, y + 14), " ".join(dtc[:3]), fill=RED, font=FONT_SMALL)

    draw_status_bar(draw, 215, "OK" if not dtc else "DTC", dtc)


def _render_infra(draw: ImageDraw.ImageDraw, link: DeviceLink, data: dict) -> None:
    """Infrastructure layout: CPU/mem/disk metrics + cost."""
    schema = link.schema
    y = draw_header(draw, link.name or link.id, link.type or "", y=0)

    # CPU — big
    cpu = data.get("cpu_pct", "--")
    cpu_color = value_color(cpu, schema.get("cpu_pct")) if isinstance(cpu, (int, float)) else WHITE
    draw_big_value(draw, 4, y, "CPU", f"{cpu}", "%", cpu_color)

    # Memory — big
    mem = data.get("mem_pct", "--")
    mem_color = value_color(mem, schema.get("mem_pct")) if isinstance(mem, (int, float)) else WHITE
    draw_big_value(draw, 124, y, "MEM", f"{mem}", "%", mem_color)

    y += 55

    # Disk
    disk = data.get("disk_pct", "--")
    draw_small_value(draw, 4, y, "Disk", f"{disk}", "%", WHITE)

    # Cost
    cost = data.get("monthly_cost_usd", "--")
    draw_small_value(draw, 124, y, "Cost", f"${cost}", "/mo", ORANGE)

    y += 40

    # Instance ID
    instance = data.get("instance_id", "")
    draw.text((4, y), instance, fill=DIM, font=FONT_TINY)

    # Alerts
    alert_count = data.get("active_alerts", 0)
    status = "OK" if alert_count == 0 else f"{alert_count} ALERTS"
    draw_status_bar(draw, 215, status, [] if alert_count == 0 else [status])


def _render_home(draw: ImageDraw.ImageDraw, link: DeviceLink, data: dict) -> None:
    """Home thermostat layout: temperature + humidity."""
    y = draw_header(draw, link.name or link.id, link.type or "", y=0)

    # Temperature — big center
    temp = data.get("temp_c", "--")
    draw_big_value(draw, 4, y, "Temp", str(temp), "\u00b0C", CYAN, width=120)

    # Target
    target = data.get("target_temp_c", "--")
    draw_big_value(draw, 124, y, "Target", str(target), "\u00b0C", DIM)

    y += 55

    # Humidity
    humidity = data.get("humidity_pct", "--")
    draw_small_value(draw, 4, y, "Humidity", str(humidity), "%", WHITE)

    # Mode
    mode = data.get("mode", "unknown")
    mode_colors = {"heating": ORANGE, "cooling": CYAN, "idle": DIM}
    mode_color = mode_colors.get(mode, WHITE)
    draw_small_value(draw, 124, y, "Mode", mode, "", mode_color)

    draw_status_bar(draw, 215, mode)


def _render_industrial(draw: ImageDraw.ImageDraw, link: DeviceLink, data: dict) -> None:
    """Industrial machine layout: pressure + temp + cycle count."""
    schema = link.schema
    y = draw_header(draw, link.name or link.id, link.type or "", y=0)

    # Pressure — big
    pressure = data.get("pressure_bar", "--")
    p_color = value_color(pressure, schema.get("pressure_bar")) if isinstance(pressure, (int, float)) else WHITE
    draw_big_value(draw, 4, y, "Pressure", str(pressure), "bar", p_color)

    y += 55

    # Temperature
    temp = data.get("temp_c", "--")
    t_color = value_color(temp, schema.get("temp_c")) if isinstance(temp, (int, float)) else WHITE
    draw_small_value(draw, 4, y, "Temp", str(temp), "\u00b0C", t_color)

    # Cycles
    cycles = data.get("cycle_count", "--")
    draw_small_value(draw, 124, y, "Cycles", str(cycles), "", WHITE)

    # Status
    status = data.get("status", "unknown")
    draw_status_bar(draw, 215, status)


def _render_generic(draw: ImageDraw.ImageDraw, link: DeviceLink, data: dict) -> None:
    """Generic key-value layout for unknown device types."""
    y = draw_header(draw, link.name or link.id, link.type or "custom", y=0)

    for key, value in data.items():
        if key == "ts":
            continue
        if y > 200:
            draw.text((4, y), "...", fill=DIM, font=FONT_SMALL)
            break

        draw.text((4, y), f"{key}:", fill=DIM, font=FONT_TINY)
        draw.text((4, y + 12), str(value), fill=WHITE, font=FONT_MEDIUM)
        y += 32

    draw_status_bar(draw, 215, "LIVE")


def render_scanning_screen() -> Image.Image:
    """Render 'Scanning for QR...' screen."""
    img = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), BLACK)
    draw = ImageDraw.Draw(img)

    draw.text((50, 90), "SCANNING", fill=CYAN, font=FONT_LARGE)
    draw.text((55, 130), "Point at QR code", fill=DIM, font=FONT_SMALL)
    draw.text((60, 150), "to connect...", fill=DIM, font=FONT_SMALL)

    return img


def render_connecting_screen(device_id: str) -> Image.Image:
    """Render 'Connecting to...' screen."""
    img = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), BLACK)
    draw = ImageDraw.Draw(img)

    draw.text((40, 90), "CONNECTING", fill=YELLOW, font=FONT_LARGE)
    draw.text((30, 130), device_id[:28], fill=DIM, font=FONT_SMALL)

    return img


def render_error_screen(message: str) -> Image.Image:
    """Render error screen."""
    img = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), BLACK)
    draw = ImageDraw.Draw(img)

    draw.text((70, 90), "ERROR", fill=RED, font=FONT_LARGE)
    # Word wrap
    words = message.split()
    line = ""
    y = 130
    for word in words:
        test = f"{line} {word}".strip()
        if len(test) > 28:
            draw.text((10, y), line, fill=WHITE, font=FONT_SMALL)
            y += 18
            line = word
        else:
            line = test
    if line:
        draw.text((10, y), line, fill=WHITE, font=FONT_SMALL)

    return img


def render_device_list(
    devices: list,
    selected_index: int = 0,
    active_id: str = "",
) -> Image.Image:
    """Render device list screen for multi-device switching.

    Args:
        devices: list of DeviceLink objects
        selected_index: currently highlighted device
        active_id: ID of the currently connected device
    """
    img = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), BLACK)
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((50, 5), "DEVICES", fill=CYAN, font=FONT_MEDIUM)
    draw.text((10, 28), f"{len(devices)} known", fill=DIM, font=FONT_TINY)
    draw.line([(0, 40), (240, 40)], fill=DIM, width=1)

    if not devices:
        draw.text((40, 100), "No devices yet", fill=DIM, font=FONT_SMALL)
        draw.text((30, 125), "Scan a QR to connect", fill=DIM, font=FONT_TINY)
        return img

    # Device list (max 5 visible)
    visible_start = max(0, selected_index - 2)
    visible_end = min(len(devices), visible_start + 5)

    y = 45
    for i in range(visible_start, visible_end):
        device = devices[i]
        is_selected = i == selected_index
        is_active = device.id == active_id

        # Selection highlight
        if is_selected:
            draw.rectangle([(0, y), (240, y + 32)], fill=(20, 40, 50))

        # Active indicator
        if is_active:
            draw.text((4, y + 2), "*", fill=GREEN, font=FONT_SMALL)

        # Device name
        name = (device.name or device.id)[:20]
        name_color = CYAN if is_selected else WHITE
        draw.text((18, y + 2), name, fill=name_color, font=FONT_SMALL)

        # Device type
        dtype = (device.type or "unknown").split(".")[-1]
        draw.text((18, y + 18), dtype, fill=DIM, font=FONT_TINY)

        # Auth badge
        if device.auth and device.auth != "open":
            draw.text((210, y + 5), "PIN", fill=YELLOW, font=FONT_TINY)

        y += 34

    # Scroll indicators
    if visible_start > 0:
        draw.text((115, 42), "^", fill=DIM, font=FONT_TINY)
    if visible_end < len(devices):
        draw.text((115, y), "v", fill=DIM, font=FONT_TINY)

    # Bottom bar
    draw.line([(0, 215), (240, 215)], fill=DIM, width=1)
    draw.text((10, 220), "ENTER=Connect", fill=GREEN, font=FONT_TINY)
    draw.text((140, 220), "ESC=Back", fill=DIM, font=FONT_TINY)

    return img
