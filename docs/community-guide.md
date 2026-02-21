# Community Guide

> **"ScouterHUD defines the interfaces. You build what connects to them."**

---

## How ScouterHUD is designed for contribution

ScouterHUD is not a monolithic product — it's a set of **interfaces** that connect independent components. Each interface is a clear contract: if your component speaks the contract, it works with the ecosystem. You don't need permission, you don't need to fork the core, and you don't need to understand the entire codebase.

This guide explains what those interfaces are, where contributions have the most impact, and what principles we ask you to respect.

---

## The interfaces

Everything in ScouterHUD connects through one of these contracts. Understanding them is the key to contributing.

### 1. QR-Link protocol (device → HUD)

```
qrlink://v1/{device_id}/mqtt/{host}:{port}?auth={level}&t={topic}
```

**The contract:** Any device that publishes JSON to an MQTT topic and provides a QR code with this URL format is instantly compatible with ScouterHUD. No driver, no plugin, no registration.

**What you need to implement:**
- Publish JSON data to an MQTT topic at a regular interval
- Publish a `$meta` retained message with device metadata (name, type, icon, fields)
- Generate a QR code encoding the `qrlink://` URL

**What you get for free:** The HUD will discover your device, authenticate if needed, subscribe to the topic, select an appropriate layout, and render your data — all from one QR scan.

See [protocol spec](../software/scouterhud/qrlink/protocol.py) and [emulator examples](../emulator/devices/) for reference implementations.

---

### 2. MQTT data format (device → HUD)

**The contract:** Publish a JSON object to your MQTT topic. Keys are field names, values are numbers or strings. The HUD renders them automatically.

```json
{
  "heart_rate": 72,
  "spo2": 98,
  "temperature": 36.5,
  "status": "stable"
}
```

**`$meta` retained message** (published once, on `{topic}/$meta`):

```json
{
  "name": "Patient Monitor Bed 12",
  "type": "medical.respiratory",
  "icon": "lungs",
  "auth": "pin",
  "fields": {
    "heart_rate": {"label": "HR", "unit": "bpm", "min": 40, "max": 200},
    "spo2": {"label": "SpO2", "unit": "%", "min": 0, "max": 100}
  }
}
```

The `type` field determines which HUD layout renders the data. Current types: `medical.*`, `vehicle.*`, `infra.*`, `home.*`, `industrial.*`, `custom.*`.

---

### 3. Bridge interface (legacy device → MQTT)

A Bridge is a small device (typically an ESP32) that translates a legacy protocol into MQTT + QR-Link.

**The contract:** Read data from the legacy device, publish it as JSON to MQTT, and serve a QR code. That's it.

**Example bridges the community could build:**

| Bridge | Input protocol | Translates to | Who needs it |
|--------|---------------|---------------|--------------|
| OBD-II Bridge | CAN bus / ELM327 | `vehicle.obd2` MQTT | Mechanics, drivers |
| HL7 Bridge | HL7v2 / FHIR | `medical.*` MQTT | Hospitals, clinics |
| Modbus Bridge | Modbus RTU/TCP | `industrial.*` MQTT | Factories, PLCs |
| BACnet Bridge | BACnet/IP | `home.*` / `infra.*` MQTT | Building automation |
| USB Serial Bridge | JSON over serial | `custom.*` MQTT | Arduino/sensor projects |
| BLE Sensor Bridge | BLE GATT | `custom.*` MQTT | Fitness, environmental |

Each bridge is an independent project. It doesn't need to import ScouterHUD code — it just needs to speak MQTT and generate a QR-Link URL. Use any language, any framework, any hardware.

The [emulator](../emulator/) is a reference implementation of the data-publishing side. Start there.

---

### 4. Frame mounting interface (physical)

The ScouterHUD frame is a headband with a standardized rail system. Modules clip onto the rail.

**The contract** (to be finalized with first hardware prototype):
- Rail profile: miniature T-slot or dovetail (exact dimensions TBD after prototyping)
- Module attachment: slide-on + locking clip (tool-free)
- Electrical interface between modules: pogo pins or flex cable (TBD)
- Weight budget per module: target <30g per clip-on unit

**Modules the community could design:**

| Module | What it does | Attaches to |
|--------|-------------|-------------|
| Visor (optics) | Display + beam splitter + lens | Front rail |
| Battery pack | LiPo + charger + regulator | Rear rail (counterweight) |
| Bone conduction speaker | Audio output without blocking ears | Side rail |
| Microphone boom | STT input for voice commands | Side rail |
| LED indicator | Status light visible to others | Any rail |
| Sun visor | Glare reduction for outdoor use | Above visor |

**Key principle:** The visor is the only module that comes with the base ScouterHUD. Everything else is optional. The frame is the platform — modules are the ecosystem.

**For 3D designers:** Every module should include STL/STEP files, a BOM (bill of materials), and assembly instructions. Use the same rail interface so modules from different designers are interchangeable. License: CERN-OHL-S v2.

---

### 5. HUD layout interface (data → pixels)

A layout defines how device data is rendered on the 240x240 HUD display.

**The contract:** A layout receives a dict of field names → values and renders them onto a 240x240 pygame Surface.

**Current layouts:**

| Type prefix | Layout | Optimized for |
|------------|--------|---------------|
| `medical.*` | Large vitals + color-coded alerts | Nurses, doctors, paramedics |
| `vehicle.*` | RPM + speed + gauges | Drivers, mechanics |
| `infra.*` | Metrics dashboard + costs | DevOps, sysadmins |
| `home.*` | Temperature + mode | Homeowners |
| `industrial.*` | Pressure + cycle count | Operators, maintenance |
| `custom.*` | Generic key-value | Anything else |

**Layouts the community could create:**

| Layout | Optimized for | Key fields |
|--------|---------------|------------|
| `aviation.*` | Pilots | Altitude, airspeed, heading, vertical speed |
| `cycling.*` | Cyclists | Speed, cadence, power, heart rate, grade |
| `diving.*` | Divers | Depth, NDL, tank pressure, ascent rate |
| `agriculture.*` | Farmers | Soil moisture, pH, temperature, irrigation status |
| `weather.*` | Meteorologists | Temp, humidity, pressure, wind, UV index |
| `energy.*` | Solar/grid | Generation, consumption, battery, grid status |

See [renderer.py](../software/scouterhud/display/renderer.py) for the current layout implementations.

**Future:** We plan to support layout definitions via YAML/JSON config files, so designers can create layouts without writing Python. Until then, layouts are Python functions in the renderer module.

---

### 6. App panel interface (phone UI)

The ScouterApp uses a panel system: full-screen views that the user swipes between.

**Current panels:** BASE (D-pad + actions), NUMPAD, ALPHA (QWERTY), AI CHAT, DEVICE LIST.

**Panels the community could create:**

| Panel | Purpose | Use case |
|-------|---------|----------|
| Drone control | Joystick + altitude + camera | Drone operators |
| Home automation | Room selector + device toggles | Smart home users |
| Medical quick-actions | Pre-set vital thresholds + alerts config | Nurses |
| Macro pad | Configurable shortcut buttons | Power users |
| Voice control | Push-to-talk + transcript display | Hands-busy scenarios |

Panels are Flutter widgets in `lib/screens/`. They communicate with the HUD via the WebSocket JSON protocol (see [websocket_service.dart](../app/flutter/scouter_app/lib/services/websocket_service.dart)).

---

## High-impact contribution areas

Not all contributions are equal. Here's where help has the most impact, roughly ordered:

### Immediate impact

1. **Device emulators** — Add realistic emulators for your industry. This lets everyone test without hardware. See [emulator/devices/](../emulator/devices/) for examples. Python, ~100 lines each.

2. **HUD layouts** — Design a layout for your domain. Medical professionals know what vitals matter. Pilots know what instruments to show. We don't — you do.

3. **Bridges** — If you work with a specific protocol (OBD-II, HL7, Modbus, BLE sensors), you can build a bridge that makes an entire class of devices compatible with ScouterHUD.

### Medium-term impact

4. **Frame and module designs** — 3D-printable frames, mounts, and clip-on modules. The frame spec will be finalized after the first hardware prototype, but exploratory designs are welcome now.

5. **App UI/UX** — Mockups, usability testing, accessibility improvements. The app is designed for operation without looking at the screen — test it blindfolded and tell us what breaks.

6. **Documentation and tutorials** — "How I mounted ScouterHUD on my welding helmet." "How I connected my aquarium sensors." Real-world guides are more valuable than API docs.

### Long-term impact

7. **LLM on-device integration** — The AI chat UI is built and working (echo stub). The blocker is Flutter + llama.cpp native bridge stability. If you have experience with native FFI in Flutter or llama.cpp mobile deployment, this is the highest-impact unsolved problem.

8. **BLE transport** — Replace WiFi/WebSocket with BLE for phone↔HUD communication. Requires the Pi Zero 2W hardware. Protocol is already transport-agnostic.

9. **Voice pipeline** — STT (Whisper) + TTS (Piper) integration for hands-free operation. Research and prototyping welcome.

---

## What we ask you to respect

### Hard rules

These are non-negotiable. Contributions that violate them will not be accepted.

1. **No camera on the base HUD.** Camera modules can exist as optional, detachable peripherals — but the default ScouterHUD ships without one. Privacy by design is a core principle, not a feature. (See [why-scouterhud.md](why-scouterhud.md) for context.)

2. **No cloud dependencies for core functionality.** The HUD must work fully offline. Bridges may use internet to reach remote MQTT brokers, but the HUD→display pipeline never depends on external services.

3. **No cloud for health/personal data.** AI inference, data processing, and storage of sensitive data must be on-device. This isn't preference — it's compliance (HIPAA, GDPR, basic trust).

4. **Open source everything.** Software: MIT. Hardware: CERN-OHL-S v2. If you contribute, your contribution inherits the project license. No proprietary modules, no "open core" with paid add-ons.

### Soft guidelines

These are strong preferences, not absolute rules. Deviate if you have a good reason, but explain why.

1. **Prefer standards over custom protocols.** MQTT, not a custom pub/sub. QR codes, not custom scanning. WebSocket, not a custom TCP. Use what exists.

2. **Optimize for $50 total BOM.** If a component can be eliminated without losing function, eliminate it. If a cheaper component works, use it.

3. **One person should be able to build it.** If your frame design requires a CNC machine, it won't reach most makers. If your bridge needs a $200 dev board, it won't reach most hackers. Design for accessibility.

4. **Test without hardware.** Emulators, mocks, preview mode. Every feature should be testable on a laptop before it touches a Pi.

---

## Repository structure

Today, ScouterHUD is a monorepo. As the community grows, components will naturally split into satellite repos.

**Core (this repo):**

```
scouterHUD/
├── software/          # HUD software (Python): state machine, renderer, input, auth
├── app/flutter/       # ScouterApp (Flutter): phone control app
├── emulator/          # Device emulators for testing
├── docs/              # Specs, protocols, guides
└── hardware/          # Frame designs (future, after first prototype)
```

**Community satellites (separate repos, when ready):**

```
scouterhud-bridge-obd2/        # OBD-II → MQTT bridge (ESP32)
scouterhud-bridge-hl7/         # HL7/FHIR → MQTT bridge
scouterhud-frame-hardhat/      # Hardhat mount STL + assembly guide
scouterhud-frame-cycling/      # Cycling helmet mount
scouterhud-layout-aviation/    # Aviation HUD layout
scouterhud-emulator-ventilator/ # Mechanical ventilator emulator
```

**When does a component get its own repo?** When it has its own maintainer, its own release cycle, and its own user base. Until then, PRs to the core repo are welcome.

**Naming convention:** `scouterhud-{type}-{name}` where type is `bridge`, `frame`, `layout`, `emulator`, `module`, or `panel`.

---

## How to start contributing

### Easiest first contribution

1. **Add a device emulator.** Pick a device from your industry. Create a Python class in `emulator/devices/` that generates realistic data. ~100 lines. See [medical_monitor.py](../emulator/devices/medical_monitor.py) as a template.

2. **Propose a layout.** Sketch (on paper, in Figma, in ASCII art) how data from your domain should look on a 240x240 display. Open an issue with the sketch. Someone will implement it.

3. **Write a use-case guide.** "How ScouterHUD could work in [your industry]." Real-world scenarios are invaluable for prioritizing features.

### Medium contributions

4. **Build a bridge.** ESP32 + your protocol → MQTT. Use the [emulator](../emulator/) as a reference for the MQTT output format. Can be done in Arduino, MicroPython, Rust, or C.

5. **Design a frame variant.** STL files + BOM + photos. Even if the rail spec isn't final, exploratory designs teach us what works.

6. **Improve the app.** Flutter. The [control_screen.dart](../app/flutter/scouter_app/lib/screens/control_screen.dart) is the main panel router. New panels go in `lib/screens/`.

### Advanced contributions

7. **Solve LLM on-device.** The UI exists. The protocol exists. What's missing is a working Flutter → llama.cpp native bridge. See [llm-attempts.md](../docs/) for what we've tried and why it failed.

8. **Implement BLE transport.** Replace WebSocket with BLE for phone↔HUD. The `PhoneInput` backend is designed for multiple transports. Needs Pi Zero 2W hardware.

---

## The vision

ScouterHUD becomes a **platform**, not a product. The core team maintains the interfaces (QR-Link protocol, MQTT format, rail spec, panel system). The community builds everything that connects to them.

A nurse in Buenos Aires designs the ideal vitals layout. A mechanic in Lagos builds an OBD-II bridge. A maker in Tokyo designs a cycling helmet mount. A student in Berlin writes a weather station emulator. None of them need to coordinate. They all just speak the interfaces.

**The best platforms don't tell you what to build. They make it obvious where to plug in.**

---

*ScouterHUD is an open source project by Ger. MIT (Software) / CERN-OHL-S v2 (Hardware).*
