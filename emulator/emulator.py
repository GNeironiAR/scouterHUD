#!/usr/bin/env python3
"""ScouterHUD Device Emulator Hub.

Runs virtual QR-Link devices that publish realistic data via MQTT.
Each device publishes metadata on {topic}/$meta (retained) and streams
data on {topic} at the configured refresh rate.

Usage:
    python emulator.py                              # all devices
    python emulator.py --device monitor-bed-12      # single device
    python emulator.py --device car-001 --scenario overheating
    python emulator.py --broker-host 192.168.1.50   # remote broker
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
from pathlib import Path

import paho.mqtt.client as mqtt
import yaml

from devices import DEVICE_TYPES
from devices.base import BaseDevice

# --- Colors for per-device logging ---
COLORS = [
    "\033[96m",  # cyan
    "\033[93m",  # yellow
    "\033[92m",  # green
    "\033[95m",  # magenta
    "\033[94m",  # blue
]
RESET = "\033[0m"
BOLD = "\033[1m"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )


def load_config(path: str = "config.yaml") -> dict:
    config_path = Path(path)
    if not config_path.exists():
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def create_device(device_config: dict, broker_host: str, broker_port: int) -> BaseDevice:
    device_type = device_config["type"]
    cls = DEVICE_TYPES.get(device_type)
    if cls is None:
        raise ValueError(f"Unknown device type: {device_type}")
    return cls(device_config, broker_host, broker_port)


def connect_mqtt(broker_host: str, broker_port: int) -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            logging.info(f"{BOLD}MQTT connected to {broker_host}:{broker_port}{RESET}")
        else:
            logging.error(f"MQTT connection failed: rc={rc}")

    def on_disconnect(client, userdata, flags, rc, properties=None):
        if rc != 0:
            logging.warning(f"MQTT disconnected unexpectedly (rc={rc}), reconnecting...")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect(broker_host, broker_port, keepalive=60)
    except ConnectionRefusedError:
        logging.error(
            f"Cannot connect to MQTT broker at {broker_host}:{broker_port}\n"
            f"Make sure Mosquitto is running:\n"
            f"  docker run -d -p 1883:1883 eclipse-mosquitto:2 "
            f"mosquitto -c /mosquitto-no-auth.conf"
        )
        sys.exit(1)

    client.loop_start()
    return client


async def run_device(
    device: BaseDevice,
    client: mqtt.Client,
    color: str,
    stop_event: asyncio.Event,
):
    """Publish metadata and then stream data for a single device."""
    label = f"{color}[{device.id}]{RESET}"

    # Publish metadata as retained message
    meta = device.get_metadata()
    meta_json = json.dumps(meta)
    client.publish(device.meta_topic, meta_json, qos=1, retain=True)
    logging.info(f"{label} $meta published on {device.meta_topic}")

    # Log QR-Link URL
    qr_url = device.get_qrlink_url()
    logging.info(f"{label} QR-Link: {BOLD}{qr_url}{RESET}")

    # Stream data
    tick = 0
    while not stop_event.is_set():
        data = device.generate_data()
        payload = json.dumps(data)
        client.publish(device.topic, payload, qos=0)

        if tick % 10 == 0:  # Log every 10th tick to avoid spam
            preview = {k: v for k, v in data.items() if k != "ts"}
            logging.info(f"{label} {preview}")

        tick += 1
        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=device.refresh_seconds
            )
        except asyncio.TimeoutError:
            pass  # Normal: timeout means keep going


async def run_all(
    devices: list[BaseDevice],
    client: mqtt.Client,
):
    stop_event = asyncio.Event()

    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    logging.info(f"{BOLD}Starting {len(devices)} device(s)...{RESET}")
    logging.info("")

    tasks = []
    for i, device in enumerate(devices):
        color = COLORS[i % len(COLORS)]
        tasks.append(run_device(device, client, color, stop_event))

    await asyncio.gather(*tasks)
    logging.info(f"{BOLD}All devices stopped.{RESET}")


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="ScouterHUD Device Emulator Hub")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--device", help="Run only this device ID")
    parser.add_argument("--scenario", help="Override scenario for the device")
    parser.add_argument("--broker-host", help="MQTT broker host (overrides config)")
    parser.add_argument("--broker-port", type=int, help="MQTT broker port (overrides config)")
    args = parser.parse_args()

    config = load_config(args.config)

    broker_host = args.broker_host or config.get("broker", {}).get("host", "localhost")
    broker_port = args.broker_port or config.get("broker", {}).get("port", 1883)

    # Resolve to localhost for connections (0.0.0.0 is for listening, not connecting)
    connect_host = "localhost" if broker_host == "0.0.0.0" else broker_host

    # Filter devices
    device_configs = config.get("devices", [])
    if args.device:
        device_configs = [d for d in device_configs if d["id"] == args.device]
        if not device_configs:
            logging.error(f"Device '{args.device}' not found in config")
            available = [d["id"] for d in config.get("devices", [])]
            logging.info(f"Available: {available}")
            sys.exit(1)

    # Override scenario if specified
    if args.scenario:
        for d in device_configs:
            d["scenario"] = args.scenario

    # Use broker_host (not connect_host) for QR URLs since QR is for external clients
    devices = [
        create_device(dc, broker_host, broker_port)
        for dc in device_configs
    ]

    logging.info(f"{BOLD}ScouterHUD Device Emulator Hub{RESET}")
    logging.info(f"Broker: {connect_host}:{broker_port}")
    logging.info(f"Devices: {len(devices)}")
    logging.info("")

    client = connect_mqtt(connect_host, broker_port)

    try:
        asyncio.run(run_all(devices, client))
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        logging.info("Disconnected from MQTT broker.")


if __name__ == "__main__":
    main()
