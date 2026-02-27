# Why This Stack

> **"Every technical decision in ScouterHUD optimizes for the same thing: a $50 device that one person can build, maintain, and trust with sensitive data."**

---

## The core constraint

ScouterHUD is built by one developer for a device that costs $50. Every technology choice must pass three filters:

1. **Can one person maintain it?** Two native codebases, a custom OS, or a compiled-only language means twice the work for the same result.
2. **Does it run on $15 hardware?** The Pi Zero 2W has 512MB RAM and a quad-core ARM at 1GHz. That's the ceiling.
3. **Does it work without cloud dependencies?** Health data, factory floors, moving vehicles — the system must function offline and keep data local.

---

## By decision

### 1. Raspberry Pi Zero 2W (not ESP32, not a phone)

**Why Pi Zero:**
- $15, full Linux, native Python, WiFi + BLE built-in, GPIO for SPI display.
- 512MB RAM is comfortable for Python + pygame + MQTT + WebSocket server.
- Massive community. Every library works. No porting, no cross-compilation headaches.

**Why not ESP32:**
- 520KB RAM. Rendering 240x240 layouts with fonts, colors, and dynamic data in C is a project in itself.
- No filesystem for fonts, configs, or logs without significant complexity.
- Great for peripherals (Bridge, Gauntlet), wrong for the brain.

**Why not a recycled smartphone:**
- No SPI/GPIO for optical display. You'd need an external screen anyway.
- Overkill in power consumption and weight for a head-mounted device.
- Android lifecycle management (battery optimization, background kill) fights against a persistent HUD process.

**Evolution path:** If power consumption or boot time become critical, an ESP32-S3 with direct display driving (~$8) is a valid future option — at the cost of rewriting the renderer in C.

---

### 2. SPI display 240x240 ST7789 + reflective optics

**Why 240x240 SPI:**
- $8-12. Tiny, light, low power. SPI is two wires from the Pi.
- 240x240 is enough for big numbers (vitals, RPM, temperature) and status text. ScouterHUD displays data, not web pages.
- ST7789 has mature Linux drivers (`st7789` Python lib, `/dev/fb1` framebuffer).

**Why beam splitter (not transparent OLED, not retinal projection):**
- Transparent OLEDs at this size don't exist at consumer prices.
- Retinal projection (like North Focals) costs thousands and requires custom optics.
- A $5 half-mirror film + a $3 aspheric lens = see-through display. Total optics cost: ~$10.

**Why not a bigger display:**
- Weight. Everything on your head is magnified. 1.3" is invisible. 2.8" is a brick.
- Power. Bigger backlight = bigger battery = more weight. Vicious cycle.
- FOV. A small display close to the eye (with a lens) covers more apparent area than a large display far away.

---

### 3. MQTT for device data transport

**Why MQTT:**
- It's the IoT standard. Period. Millions of devices already speak it.
- Pub/sub decouples producers from consumers. The HUD doesn't care if data comes from an OBD-II dongle, a medical monitor, or a thermostat. It subscribes to a topic and renders.
- Retained messages solve the metadata problem: `$meta` is always available, even if the device published it hours ago.
- Mosquitto is free, runs on a Pi, runs in Docker, runs everywhere.

**Why not HTTP polling:**
- Latency. Polling at 1s means up to 1s delay. MQTT push is ~50ms.
- Overhead. HTTP headers per request vs. MQTT's 2-byte fixed header.
- Not push. The HUD would burn CPU asking "any new data?" repeatedly.

**Why not WebSocket direct from each device:**
- Each device would need to run a WebSocket server. A $2 temperature sensor can't do that.
- No retained messages, no wildcard subscriptions, no broker-level QoS.
- MQTT already exists and works. Don't reinvent it.

**Why not BLE direct from device to HUD:**
- Range: ~10m vs. WiFi/internet. Useless for a server in a datacenter or a medical monitor across the ward.
- Not every device has BLE. But any device can publish to MQTT (even via a $8 ESP32 Bridge).
- BLE is peer-to-peer. MQTT is many-to-one. The HUD monitors multiple devices simultaneously.

---

### 4. QR-Link as the pairing protocol

**Why QR codes:**
- Universal. Any printer, any screen, any phone camera can generate and read them.
- Zero configuration. No app store, no account, no Bluetooth pairing dance.
- Offline. Works in a basement with no internet. The URL is self-contained.
- One scan carries everything: device ID, broker address, topic, auth level.

```
qrlink://v1/{id}/mqtt/{host}:{port}?auth={auth}&t={topic}
```

**Why not NFC:**
- Requires an NFC tag on every device ($0.30 each, but also requires programming each one).
- Range: 4cm. You have to physically touch the device. A QR on a wall works from across the room.
- Not every phone has NFC. Every phone has a camera.

**Why not Bluetooth pairing:**
- The UX is terrible: "searching... found 47 devices... which one is `BLE-Device-A7:3F`?"
- Carries no metadata. After pairing, you still need a second protocol to exchange broker/topic info.
- QR-Link encodes the full connection recipe in one scan. Bluetooth pairing is just a handshake.

**Why a custom protocol (not just a URL):**
- `qrlink://` is a custom scheme so the ScouterApp can register as a handler.
- The compact format (`v1/{id}/mqtt/{host}:{port}?auth=...&t=...`) fits in a small QR code — important for printing on equipment labels.
- It's extensible: `v2` can add fields without breaking `v1` scanners.

---

### 5. Flutter for the phone app (not native, not React Native, not PWA)

**Why Flutter:**
- One codebase for Android + iOS. One developer can't maintain two native apps.
- Custom widgets are first-class. The D-pad, QWERTY keyboard, and device list are all custom-drawn — Flutter makes this trivial with `Container`, `GestureDetector`, and `CustomPaint`.
- Dart compiles to native ARM. No JavaScript bridge, no runtime overhead.
- Direct access to platform APIs: camera (QR scanning), biometrics (local_auth), BLE (future).

**Why not React Native:**
- JS bridge adds latency to every touch event. For a control surface used while not looking at the screen, 16ms matters.
- Custom native widgets require writing bridge code in Java/Kotlin + Objective-C/Swift. Flutter's widget system is self-contained.
- The React Native ecosystem fragments across Expo, bare workflow, and third-party native modules. Flutter's toolchain is unified.

**Why not native (Kotlin + Swift):**
- Two codebases, two languages, two build systems, two sets of platform-specific bugs. One person. The math doesn't work.
- The app's logic is identical on both platforms. There's no platform-specific feature that justifies separate implementations.

**Why not a PWA (Progressive Web App):**
- No BLE access (needed for future HUD communication).
- No reliable biometric authentication (Web Authentication API is limited).
- No camera access with the reliability needed for QR scanning in the field.
- A web app was the Phase A0 proof-of-concept. Flutter replaced it because native APIs matter.

**Known trade-off:** Flutter's native plugin ecosystem can be immature. We experienced this firsthand — both `llama_cpp_dart` and `flutter_llama` crashed at the C++ bridge level with unfixable native segfaults. For standard platform APIs (camera, auth, BLE), the ecosystem is solid. For cutting-edge native ML inference, it's not there yet.

---

### 6. Python for the HUD software (not C++, not Rust, not Go)

**Why Python:**
- Prototyping speed. The full HUD software (state machine, renderer, auth, input, networking) was built in days, not months.
- pygame handles the 240x240 display rendering, font loading, and image export trivially.
- asyncio + websockets + paho-mqtt = the entire networking stack in <200 lines.
- The Pi Zero 2W runs Python natively. No cross-compilation, no toolchain setup.
- 167 tests run in <0.3 seconds. Fast iteration.

**Why not C++:**
- Development time is 5-10x longer for the same functionality.
- The display refreshes at ~2 FPS (data update rate). There's no performance bottleneck that justifies C++.
- Memory usage is ~30MB. The Pi has 512MB. Headroom for days.

**Why not Rust:**
- Steeper learning curve, smaller IoT library ecosystem than Python.
- The borrow checker is valuable for systems programming. For a state machine that renders text on a 240x240 display, it's overhead without benefit.
- No pygame equivalent. Display rendering would require raw framebuffer manipulation or a custom solution.

**Why not Go:**
- Similar to Rust: good language, wrong problem. The concurrency model is overkill for a single-display device.
- No mature pygame-equivalent for rendering.
- Deployment on Pi Zero works but the Go binary + runtime is larger than the Python interpreter already on the device.

**Evolution path:** If Python's startup time (~1s) or memory footprint (~30MB) becomes a problem on constrained hardware, a C port of the renderer alone would be the surgical fix — not a full rewrite.

---

### 7. WebSocket for phone-to-HUD communication (staging for BLE)

**Why WebSocket now:**
- Bidirectional, low latency (~5ms on LAN), works over WiFi.
- The web PoC (Phase A0) used it, so the protocol was already proven.
- Testable without hardware: any laptop can run the HUD software, any phone on the same WiFi can connect.
- The JSON message protocol on top is transport-agnostic. Switching from WebSocket to BLE changes one layer, not the whole stack.

**Why not BLE from the start:**
- BLE requires the Pi Zero 2W hardware to test. WebSocket lets us develop and test everything on a laptop.
- WiFi has more range and throughput than BLE. For development and demo scenarios, this matters.
- The BLE transport is planned for production. WebSocket is the development transport. Both carry the same JSON protocol.

**Why not REST API:**
- Not bidirectional. The HUD needs to push state changes to the phone (numeric mode, device list, errors).
- Polling wastes bandwidth and adds latency.
- WebSocket is a single persistent connection. REST would be a new TCP handshake per request.

**Production path:** BLE replaces WebSocket when hardware is available. The `PhoneInput` backend abstraction already supports multiple transports — BLE will be a new backend alongside WebSocket, not a replacement.

---

### 8. Phone as primary input (not buttons on the HUD)

**Why the phone:**
- It already has a touchscreen, camera, biometric sensor, keyboard, microphone, and speakers. Adding any of these to the HUD would increase cost, weight, and complexity.
- The phone is always in the user's pocket. No extra hardware to carry.
- Software updates to the input interface are an APK install, not a hardware revision.

**Why not buttons/touch on the HUD:**
- Every gram on your head matters. A touchpad + driver + wiring = 10-15g more.
- Buttons on a head-mounted device are ergonomically awkward. You'd be poking your own temple.
- The phone screen is at arm's length in landscape — a natural control surface.

**Why the Gauntlet exists (ESP32 bracelet):**
- Edge cases: thick industrial gloves, IP67 wet environments, users without a phone.
- It's an optional accessory, not the primary input. 90% of users won't need it.
- BLE capacitive pads on the wrist = input without removing gloves or pulling out a phone.

---

### 9. No camera on the HUD (privacy by design)

**Why no camera:**
- Google Glass died because of the camera. "Glasshole" entered the dictionary. Hospitals, courtrooms, and factories banned it.
- A wearable without a camera can go anywhere. No legal issues, no social stigma, no access restrictions.
- Less hardware = less weight, less power consumption, less cost, fewer failure points.

**How QR scanning works without a HUD camera:**
- The phone's camera scans QR codes. The phone sends the decoded URL to the HUD via WebSocket.
- The phone camera is socially acceptable — everyone already uses their phone to scan things.
- Separating the camera from the always-on display is a deliberate architectural choice: the display is passive (shows data), the camera is active (requires intent).

---

### 10. LLM on-device (not cloud, not LAN)

**Why on-device:**
- Health data (vitals, patient info) is PII/PHI. Sending it to a cloud API violates HIPAA, GDPR, and basic trust.
- A LAN server (local PC running inference) isn't portable. A mechanic, a driver, a nurse walking the ward — none of them have a local server nearby.
- The phone has 6-12GB RAM and a capable NPU/GPU. The hardware can run a 1-3B parameter model.

**Current status: working.**
- `flutter_gemma` v0.11.16 + Gemma 3 1B IT int4 (~529 MB .task file). Runs on-device, GPU-accelerated, streaming responses.
- **Context-aware**: live sensor data from the connected device is injected into the LLM context. The AI can answer questions about what the user is seeing ("what's the heart rate?", "is the coolant temp normal?").
- Model hosted on GitHub Releases (~529 MB one-time download, no network needed after that).
- Previous failed attempts: `llama_cpp_dart` (build failures), `flutter_llama` v1.1.2 (native segfaults in llama.cpp C++ bridge).

**Why not a cloud API as a fallback:**
- It's not about preference — it's about compliance. One leaked vitals packet = legal liability.
- If we allow cloud for "non-sensitive" data, the boundary becomes blurry. Better to draw a hard line: all inference is local, always.

**Why not a hybrid (cloud for non-medical, local for medical):**
- Increases complexity (two inference paths, content classification, routing logic).
- Users won't understand the distinction. "Why does AI work for my car but not for grandma's heart monitor?"
- One simple rule is better than a complex conditional.

---

## The stack at a glance

| Component | Choice | Why |
|-----------|--------|-----|
| HUD processor | Pi Zero 2W | $15, Linux, Python, WiFi+BLE, GPIO |
| Display | ST7789 240x240 SPI | $8, tiny, low power, mature drivers |
| Optics | Beam splitter + aspheric lens | $10, only viable see-through at this price |
| Data transport | MQTT (Mosquitto) | IoT standard, pub/sub, retained messages |
| Pairing protocol | QR-Link (custom URL scheme) | Zero-config, offline, self-contained |
| Phone app | Flutter (Dart) | One codebase, custom widgets, native APIs |
| HUD software | Python (pygame, asyncio) | Fast prototyping, Pi-native, 190 tests in 0.3s |
| Phone-HUD comm | WebSocket (staging for BLE) | Bidirectional, testable without hardware |
| Input | Phone (primary), Gauntlet ESP32 (optional) | Phone has everything; Gauntlet for edge cases |
| Camera | None on HUD, phone camera for QR | Privacy by design, social acceptance |
| AI/LLM | On-device: flutter_gemma + Gemma 3 1B (working) | PII/compliance, no cloud, no LAN |
| Licensing | MIT (software) + CERN-OHL-S v2 (hardware) | Open source + open hardware, copyleft for HW |

---

## Design principles behind the choices

1. **Prototype with accessible tools, optimize later.** Python now, C later if needed. WebSocket now, BLE when hardware arrives. Get it working first.
2. **One person must be able to build and maintain everything.** Flutter over native. Python over C++. Mono-repo over microservices.
3. **Privacy is not a feature — it's a constraint.** No camera. No cloud. No exceptions.
4. **Standards over custom protocols.** MQTT, not a custom pub/sub. QR codes, not a custom scanning system. WebSocket, not a custom TCP protocol. Custom only where no standard exists (QR-Link).
5. **The cheapest correct solution wins.** $50 total BOM. If a component can be eliminated without losing function, eliminate it.

---

*ScouterHUD is an open source project by Ger. MIT (Software) / CERN-OHL-S v2 (Hardware).*
