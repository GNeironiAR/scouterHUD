#!/usr/bin/env python3
"""Generate QR codes for all devices defined in config.yaml.

Outputs:
  - Individual PNG files in qr_output/ (one per device)
  - A single printable A4 PDF with all QR codes (6 per page)

Usage:
    python generate_all_qrs.py
    python generate_all_qrs.py --config config.yaml --output qr_output/
"""

import argparse
import sys
from pathlib import Path

import qrcode
import yaml
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from devices import DEVICE_TYPES
from devices.base import BaseDevice


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def create_device_for_qr(device_config: dict, broker_host: str, broker_port: int) -> BaseDevice:
    device_type = device_config["type"]
    cls = DEVICE_TYPES.get(device_type)
    if cls is None:
        raise ValueError(f"Unknown device type: {device_type}")
    return cls(device_config, broker_host, broker_port)


def generate_qr_image(data: str, label: str, sublabel: str, size: int = 400) -> Image.Image:
    """Generate a QR code image with a label below it."""
    qr = qrcode.QRCode(
        version=None,  # auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((size, size), Image.NEAREST)

    # Create card with label
    card_height = size + 80
    card = Image.new("RGB", (size, card_height), "white")
    card.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(card)

    # Use default font (monospace-like)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = font_large

    # Draw label centered below QR
    label_bbox = draw.textbbox((0, 0), label, font=font_large)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text(((size - label_width) / 2, size + 8), label, fill="black", font=font_large)

    sublabel_bbox = draw.textbbox((0, 0), sublabel, font=font_small)
    sublabel_width = sublabel_bbox[2] - sublabel_bbox[0]
    draw.text(((size - sublabel_width) / 2, size + 32), sublabel, fill="gray", font=font_small)

    return card


def generate_pdf(qr_cards: list[tuple[Image.Image, str]], output_path: str):
    """Generate a printable A4 PDF with QR codes, 6 per page (2 cols x 3 rows)."""
    page_w, page_h = A4  # 595 x 842 points
    margin = 20 * mm
    cols = 2
    rows = 3
    per_page = cols * rows

    card_w = (page_w - 2 * margin - 10 * mm) / cols
    card_h = (page_h - 2 * margin - 20 * mm) / rows

    c = canvas.Canvas(output_path, pagesize=A4)

    for page_start in range(0, len(qr_cards), per_page):
        page_items = qr_cards[page_start:page_start + per_page]

        for idx, (card_img, device_id) in enumerate(page_items):
            col = idx % cols
            row = idx // cols

            x = margin + col * (card_w + 5 * mm)
            y = page_h - margin - (row + 1) * card_h - row * 5 * mm

            # Save card as temp file and draw on PDF
            temp_path = f"/tmp/scouterhud_qr_{device_id}.png"
            card_img.save(temp_path)
            c.drawImage(
                temp_path, x, y,
                width=card_w, height=card_h,
                preserveAspectRatio=True,
            )

        if page_start + per_page < len(qr_cards):
            c.showPage()

    c.save()


def main():
    parser = argparse.ArgumentParser(description="Generate QR codes for ScouterHUD devices")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--output", default="qr_output", help="Output directory")
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    broker_host = config.get("broker", {}).get("host", "0.0.0.0")
    broker_port = config.get("broker", {}).get("port", 1883)

    device_configs = config.get("devices", [])
    if not device_configs:
        print("No devices found in config.")
        sys.exit(1)

    qr_cards: list[tuple[Image.Image, str]] = []

    print(f"Generating QR codes for {len(device_configs)} devices...\n")

    for dc in device_configs:
        device = create_device_for_qr(dc, broker_host, broker_port)
        qr_url = device.get_qrlink_url()

        print(f"  [{device.id}]")
        print(f"    Name: {device.name}")
        print(f"    Type: {device.type}")
        print(f"    URL:  {qr_url}")
        print(f"    Len:  {len(qr_url)} bytes")

        card = generate_qr_image(
            data=qr_url,
            label=device.name,
            sublabel=f"{device.type} | {device.auth}",
        )

        # Save individual PNG
        png_path = output_dir / f"{device.id}.png"
        card.save(str(png_path))
        print(f"    PNG:  {png_path}")
        print()

        qr_cards.append((card, device.id))

    # Generate PDF
    pdf_path = output_dir / "ALL_DEVICES_printable.pdf"
    generate_pdf(qr_cards, str(pdf_path))
    print(f"PDF generated: {pdf_path}")
    print(f"\nDone! {len(qr_cards)} QR codes generated in {output_dir}/")


if __name__ == "__main__":
    main()
