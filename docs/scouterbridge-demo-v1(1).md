# ScouterBridge — Demo v1: Vehicle Data via ELM327

## Overview

The first functional demo of ScouterBridge leverages an existing ELM327 OBD-II Bluetooth scanner as the vehicle data source, eliminating the need for direct CAN bus wiring during initial validation. This approach demonstrates the Bridge's core value proposition — protocol translation — with zero physical modification to the vehicle.

## Available OBD-II Scanner

- **Model:** HANDA OBD2 M-H149
- **Chipset:** ELM327 clone (v2.1)
- **Connectivity:** Bluetooth Classic (SPP) — NOT BLE
- **Effective range:** ~10 meters
- **Supported protocols:**
  - SAE J1850 PWM (41.6 Kbaud)
  - SAE J1850 VPW (10.4 Kbaud)
  - ISO 9141-2 (5 baud init, 10.4 Kbaud)
  - ISO 14230-4 KWP (5 baud init, 10.4 Kbaud)
  - ISO 14230-4 KWP (fast init, 10.4 Kbaud)
  - ISO 15765-4 CAN (11 bit ID, 500 Kbaud)
  - ISO 15765-4 CAN (29 bit ID, 500 Kbaud)
  - ISO 15765-4 CAN (11 bit ID, 250 Kbaud)
  - ISO 15765-4 CAN (29 bit ID, 250 Kbaud)
- **Vehicle coverage:** OBD-II compliant gasoline vehicles (1996+), light diesel ≤6.5T
- **Compatible apps:** Torque, Car Scanner ELM, DashCommand, OBD Auto Doctor
- **Known limitations:** ELM327 v2.1 clones may produce fake responses on some advanced PIDs; requires robust error handling and timeout management on the ESP32-S3 side

## Architecture

### Demo v1 — ELM327 (wireless, no direct wiring)

```
┌─────────┐    OBD-II    ┌─────────┐    BT/BLE    ┌───────────┐    BLE    ┌────────────┐
│  Auto   │◄────────────►│ ELM327  │◄────────────►│  ESP32-S3 │◄────────►│ ScouterHUD │
│  (ECU)  │   physical   │ Scanner │   wireless   │  (Bridge) │  Scouter │  (RPi Z2W) │
└─────────┘              └─────────┘              └───────────┘ Protocol └────────────┘
```

### Future v2 — Direct CAN (lower latency, no middleman)

```
┌─────────┐    OBD-II    ┌──────────────────┐    BLE    ┌────────────┐
│  Auto   │◄────────────►│ ESP32-S3         │◄────────►│ ScouterHUD │
│  (ECU)  │   pigtail    │ + MCP2515/TJA1050│  Scouter │  (RPi Z2W) │
└─────────┘              └──────────────────┘ Protocol └────────────┘
```

## Communication Flow (Demo v1)

### ESP32-S3 → ELM327 (AT Commands via Bluetooth Classic SPP)

> **Note:** The ESP32-S3 connects to the HANDA M-H149 using Bluetooth Classic Serial Port Profile (SPP), not BLE. The ESP32-S3 supports both protocols natively via `BluetoothSerial` library.

| Command | Description         | Response Example  |
|---------|---------------------|-------------------|
| `ATZ`   | Reset ELM327        | `ELM327 v2.1`    |
| `ATE0`  | Disable echo        | `OK`              |
| `ATL0`  | Disable linefeeds   | `OK`              |
| `ATSP0` | Auto-detect protocol| `OK`              |
| `010C`  | Engine RPM          | `41 0C 1A F8`    |
| `010D`  | Vehicle speed (km/h)| `41 0D 3C`       |
| `0105`  | Coolant temperature | `41 05 7B`       |
| `0104`  | Engine load         | `41 04 4E`       |

**Error handling for v2.1 clones:**
- Implement 2-second timeout per AT command
- Retry up to 3 times on `NO DATA` or `UNABLE TO CONNECT` responses
- Validate response format before parsing (expect `41 XX` prefix)
- Some PIDs may return fake/static data — cross-validate with known good app (Torque) first

### ESP32-S3 → ScouterHUD (Scouter Protocol via BLE)

The Bridge parses raw OBD-II responses, converts them to human-readable values, and packages them into Scouter Protocol frames for the HUD to render on the see-through display.

**Example data pipeline:**

```
ELM327 response: "41 0C 1A F8"
├── Parse: PID 0x0C = RPM → ((0x1A * 256) + 0xF8) / 4 = 1726 RPM
├── Package: { "type": "vehicle", "pid": "rpm", "value": 1726, "unit": "rpm" }
└── Transmit: BLE GATT characteristic → ScouterHUD
```

## Demo v1 Target PIDs

| PID    | Metric              | Unit | HUD Display Priority |
|--------|---------------------|------|----------------------|
| `010C` | Engine RPM          | rpm  | HIGH                 |
| `010D` | Vehicle Speed       | km/h | HIGH                 |
| `0105` | Coolant Temperature | °C   | MEDIUM               |
| `0104` | Engine Load         | %    | MEDIUM               |
| `012F` | Fuel Level          | %    | LOW                  |
| `0111` | Throttle Position   | %    | LOW                  |

## Hardware Required (Demo v1)

| Component | Source | Role |
|-----------|--------|------|
| ESP32-S3 (Waveshare or SuperMini) | Amazon (purchased) | Bridge MCU |
| ELM327 OBD-II scanner | Already owned | Vehicle data source |
| ScouterHUD (RPi Zero 2WH + display) | Amazon (purchased) | Data visualization |

> **Note:** The MCP2515 + TJA1050 modules and OBD-II pigtail connectors (already purchased) are reserved for Demo v2 direct CAN integration.

## Advantages of This Approach

- **Zero risk:** No direct electrical connection to vehicle CAN bus
- **Fast validation:** Proves the Bridge concept without custom wiring
- **Reusable scanner:** ELM327 serves as both testing tool and demo data source
- **Protocol agnostic:** Scanner handles J1850/CAN negotiation, Bridge focuses on translation
- **Both paths available:** v1 (ELM327) and v2 (direct CAN) hardware already procured

## Success Criteria

1. ESP32-S3 establishes BT connection with ELM327 autonomously
2. Bridge reads ≥3 PIDs from a running vehicle
3. Data is translated and transmitted to ScouterHUD via BLE
4. HUD renders live vehicle data on the see-through display
5. End-to-end latency under 500ms (acceptable for non-safety HUD data)

## Next Steps

1. ~~Confirm ELM327 Bluetooth type (Classic SPP vs BLE)~~ → **Confirmed: Bluetooth Classic SPP**
2. Validate HANDA M-H149 PID responses with Torque app (identify any fake/unreliable PIDs)
3. Implement ESP32-S3 ELM327 AT command driver (BluetoothSerial + SPP)
4. Define Scouter Protocol BLE GATT service for vehicle data
5. Build HUD overlay renderer for vehicle metrics
6. Bench test with ELM327 + vehicle before full integration
