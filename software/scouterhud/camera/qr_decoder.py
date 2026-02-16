"""QR code detection and decoding using pyzbar.

Backend-agnostic: works with any CameraBackend that returns PIL Images.
"""

import logging

from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol

log = logging.getLogger(__name__)


def scan_qr(image: Image.Image) -> str | None:
    """Scan a PIL Image for QR codes. Returns decoded string or None."""
    # Convert to grayscale for faster detection
    gray = image.convert("L")

    results = decode(gray, symbols=[ZBarSymbol.QRCODE])

    if results:
        data = results[0].data.decode("utf-8")
        log.debug(f"QR detected: {data[:80]}...")
        return data

    return None
