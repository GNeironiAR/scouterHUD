# ScouterHUD — Estado del Proyecto

**Última actualización:** 2026-02-24

---

## Análisis de compatibilidad del ecosistema

Revisión cruzada de `ecosystem-overview.md`, `bridge-tech-doc.md` y `gauntlet-tech-doc.md` contra lo implementado.

### Compatible (ya funciona)

| Aspecto | Detalle |
|---------|---------|
| QR-Link protocol | Formato compacto implementado, mismo que usará el Bridge |
| MQTT transport | Pub/sub funcional, compatible con Bridge y emulador |
| Device types + layouts | 6 layouts cubren todos los tipos del ecosistema |
| `$meta` metadata | Retained messages con schema, icon, auth_hint |
| Repo structure | `emulator/`, `software/` listos; `bridge/`, `gauntlet/` se agregan al mismo nivel |
| Bridge → HUD data flow | Un Bridge real sería idéntico al emulador desde el HUD |

### Gaps (hay que construir)

| Gap | Componente | Necesario para | Estado |
|-----|-----------|----------------|--------|
| ~~Sistema de input~~ | ~~`software/scouterhud/input/`~~ | ~~App, Gauntlet, voz, navegación~~ | **Completado** |
| ~~BLE client (Pi ↔ input)~~ | ~~`input/gauntlet_input.py` con bleak~~ | ~~Recibir eventos de App/Gauntlet~~ | **Stub listo** (necesita HW) |
| ~~PIN/TOTP auth flow~~ | ~~`software/scouterhud/auth/`~~ | ~~QR-Link auth Nivel 1-2~~ | **Completado** |
| ~~Multi-device switching~~ | ~~Ampliar `ConnectionManager`~~ | ~~Swipe entre dispositivos~~ | **Completado** |
| ~~Unit tests~~ | ~~`software/tests/`~~ | ~~Validación automática~~ | **211 tests passing** |
| ~~ScouterApp (PoC)~~ | ~~`app/web/` WebSocket + HTML~~ | ~~Input principal del ecosistema~~ | **Completado** |
| ~~ScouterApp (Flutter)~~ | ~~`app/flutter/`~~ | ~~App nativa Android/iOS~~ | **v0.4.0 — Completado** |
| Tactile overlay | `app/overlay/` STL + molde silicona | Operación a ciegas / con guantes | Después de la app |
| ~~AI Chat local (LLM on-device)~~ | ~~`app/flutter/` LlmService~~ | ~~Asistente AI sin cloud (PII/compliance)~~ | **Completado — flutter_gemma + Gemma 3 1B** |
| AI Context awareness | `app/flutter/` LlmService | AI con acceso a datos del HUD en tiempo real | Pendiente |
| Voice/AI pipeline | `software/scouterhud/input/voice.py` | Asistente por voz, STT/TTS | Baja (post-MVP) |
| Gauntlet firmware | `gauntlet/firmware/` (ESP32, PlatformIO) | Accesorio opcional (guantes gruesos, IP67) | Baja (opcional) |
| Bridge firmware | `bridge/firmware/` (ESP32, PlatformIO) | Hardware del Bridge | Cuando llegue el ESP32 |
| SPI display backend | `display/backend_spi.py` (ST7789) | HUD real en Pi Zero 2W | Cuando llegue el hardware |
| PiCamera backend | `camera/backend_pi.py` | QR scan en HUD (opcional, ver [camera-tech-doc](camera-tech-doc.md)) | Baja (opcional — privacidad) |
| ~~QR scan desde App~~ | ~~`app/` + `PhoneInput`~~ | ~~QR scanning principal (cámara del celular)~~ | **Completado (Phase A0)** |
| **Auth biométrica** | `app/` | FaceID/huella reemplaza PIN/TOTP manual | **Incluido en Phase A1** |

---

## Phase 0 — Proof of Concept: Óptica
**Estado:** Pendiente (esperando hardware)

- [ ] Soldar headers al Pi Zero 2W
- [ ] Conectar display ST7789 por SPI
- [ ] Experimentar con beam splitter (comprar 2-3 opciones)
- [ ] Probar lentes asféricas
- [ ] Validar legibilidad see-through

### Hardware necesario (ScouterHUD)

| # | Componente | Para qué | Estimado |
|---|-----------|----------|----------|
| 1 | Raspberry Pi Zero 2W | Procesador principal del HUD | ~$15 |
| 2 | Display ST7789 1.3" 240x240 SPI | Pantalla del HUD | ~$8-12 |
| 3 | Beam splitter / half mirror film | Pantalla semitransparente | ~$5-10 |
| 4 | Lente asférica 25-30mm | Enfocar display a distancia corta | ~$3-5 |
| 5 | MicroSD 16GB+ | OS + software | ~$5 |
| 6 | Batería LiPo 3.7V 2000-3000mAh | Alimentación (~5-10 hrs) | ~$8-12 |
| 7 | Regulador step-up 5V (MT3608 o similar) | LiPo 3.7V → 5V para Pi | ~$2 |
| 8 | Cargador TP4056 USB-C | Cargar batería | ~$1-2 |
| 9 | Cable flex FPC / jumper wires | Conexión SPI al display | ~$2 |
| 10 | Filamento PLA/PETG | Imprimir housing óptico | ~$5 (parcial) |

**Subtotal ScouterHUD: ~$40-55 USD** (sin cámara — ver [camera-tech-doc.md](camera-tech-doc.md) para módulo opcional +$12-17)

> **Nota de privacidad:** La cámara fue removida del HUD base por una decisión deliberada de privacidad. Un wearable con cámara genera desconfianza, problemas legales, y prohibiciones de acceso. El escaneo QR se hace desde la ScouterApp (cámara del celular). Ver [camera-tech-doc.md](camera-tech-doc.md).

### Hardware necesario (ScouterApp — input principal)

| # | Componente | Para qué | Estimado |
|---|-----------|----------|----------|
| 1 | Smartphone (Android/iOS) | El usuario ya tiene uno | $0 |
| 2 | Strap/muñequera para celular | Montar celular en antebrazo (landscape) | ~$5-10 |
| 3 | Tactile overlay (opcional) | Membrana silicona con relieves para uso a ciegas/guantes | ~$3-5 (silicona + molde 3D) |

**Subtotal ScouterApp: ~$5-15 USD** (o $0 si solo usas la app sin strap)

### Hardware necesario (ScouterGauntlet — opcional, casos extremos)

| # | Componente | Para qué | Estimado |
|---|-----------|----------|----------|
| 1 | ESP32-S3 Mini (N4R2, con USB OTG) | MCU con touch capacitivo + BLE | ~$4-6 |
| 2 | LiPo 3.7V 400mAh (503030) | Batería del brazalete | ~$3 |
| 3 | TP4056 USB-C módulo | Cargador | ~$1 |
| 4 | Micro motor vibración coin 10mm | Feedback háptico | ~$1 |
| 5 | 2N7000 MOSFET | Controlar motor vibración | ~$0.10 |
| 6 | PCB prototipo o perfboard | Montar pads + ESP32 | ~$2-3 |
| 7 | Cinta de cobre adhesiva | Pads táctiles capacitivos (prototipo) | ~$3 |
| 8 | Velcro strap 25mm | Correa del brazalete | ~$2 |

**Subtotal ScouterGauntlet: ~$15-20 USD** (solo para guantes gruesos, IP67, sin celular)

### Hardware necesario (ScouterBridge — MVP USB Serial)

| # | Componente | Para qué | Estimado |
|---|-----------|----------|----------|
| 1 | ESP32-S3 Mini (N4R2, con USB OTG) | MCU con USB Host + WiFi | ~$4-6 |
| 2 | Conector USB-A macho | Conectar al dispositivo legacy | ~$0.50 |
| 3 | Conector USB-C hembra | Power/config | ~$0.50 |
| 4 | LED RGB o bicolor | Status indicator | ~$0.20 |
| 5 | Regulador AMS1117-3.3 | 5V → 3.3V | ~$0.20 |
| 6 | PCB prototipo | Montar componentes | ~$2-3 |

**Subtotal Bridge USB MVP: ~$8-12 USD**

---

## Phase 1 — QR-Link MVP

### Device Emulator Hub
**Estado:** Completado

Componente funcional que simula dispositivos IoT publicando datos realistas por MQTT.

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `emulator/pyproject.toml` | Dependencias: paho-mqtt, pyyaml, qrcode, reportlab, Pillow | Listo |
| `emulator/config.yaml` | 5 dispositivos de demo con escenarios configurables | Listo |
| `emulator/generators/realistic_data.py` | SignalGenerator, CorrelatedSignal, CycleGenerator, AlertInjector, DrainingSignal | Listo |
| `emulator/devices/base.py` | BaseDevice ABC: generate_data(), get_metadata(), get_qrlink_url() | Listo |
| `emulator/devices/medical_monitor.py` | Monitor respiratorio (stable_patient, gradual_decline, sudden_alert) | Listo |
| `emulator/devices/vehicle_obd2.py` | OBD-II (city_driving, highway, idle, overheating) | Listo |
| `emulator/devices/server_infra.py` | Servidor cloud (normal_load, spike, cost_alert) | Listo |
| `emulator/devices/home_thermostat.py` | Termostato (daily_cycle) | Listo |
| `emulator/devices/industrial_machine.py` | Prensa hidráulica (production_cycle) | Listo |
| `emulator/emulator.py` | Orquestador: CLI args, asyncio, MQTT publish, logging con colores | Listo |
| `emulator/generate_all_qrs.py` | Genera PNGs individuales + PDF A4 imprimible | Listo |

**Formato QR-Link implementado:**
```
qrlink://v1/{id}/mqtt/{host}:{port}?auth={auth}&t={topic}
```

### Desktop Display Emulator + ScouterHUD Software
**Estado:** Completado

Software principal del ScouterHUD con display emulado en desktop.

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `software/scouterhud/display/backend.py` | ABC DisplayBackend (240x240) | Listo |
| `software/scouterhud/display/backend_desktop.py` | DesktopBackend: pygame 240x240 escalado 3x | Listo |
| `software/scouterhud/display/backend_preview.py` | PreviewBackend: guarda PNG en /tmp para WSL2 | Listo |
| `software/scouterhud/display/widgets.py` | Widgets: draw_big_value, draw_small_value, draw_header, draw_status_bar, value_color | Listo |
| `software/scouterhud/display/renderer.py` | Layout engine: 6 layouts + device list + pantallas de estado | Listo |
| `software/scouterhud/camera/backend.py` | ABC CameraBackend | Listo |
| `software/scouterhud/camera/backend_desktop.py` | DesktopCameraBackend: webcam (OpenCV) o archivo QR | Listo |
| `software/scouterhud/camera/qr_decoder.py` | QR scanning con pyzbar (requiere `libzbar0`) | Listo |
| `software/scouterhud/qrlink/protocol.py` | Parser URL compacta `qrlink://v1/...` + DeviceLink dataclass | Listo |
| `software/scouterhud/qrlink/transports/mqtt.py` | MQTTTransport: connect, fetch $meta, subscribe data stream | Listo |
| `software/scouterhud/qrlink/connection.py` | ConnectionManager: multi-device history + switching | Listo |
| `software/scouterhud/main.py` | Entry point CLI con state machine: --scan, --demo, --preview, --auth, --phone | Listo |

### Sistema de Input
**Estado:** Completado

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `software/scouterhud/input/events.py` | EventType enum (35 tipos: +ALPHA_KEY/BACKSPACE/ENTER/SHIFT, AI_CHAT_MESSAGE, BIOMETRIC_AUTH) + InputEvent dataclass | Listo |
| `software/scouterhud/input/backend.py` | ABC InputBackend (start, stop, poll) | Listo |
| `software/scouterhud/input/keyboard_input.py` | KeyboardInput (pygame) + StdinKeyboardInput (preview/wasd) | Listo |
| `software/scouterhud/input/input_manager.py` | InputManager: poll N backends, toggle modo numérico | Listo |

**Controles implementados:**

*Teclado (preview mode: w/a/s/d):*

| Tecla | Acción (modo navegación) | Acción (modo PIN) |
|-------|--------------------------|-------------------|
| `w` / `↑` | NAV_UP | Incrementar dígito (+) |
| `s` / `↓` | NAV_DOWN | Decrementar dígito (−) |
| `a` / `←` | NAV_LEFT | Dígito anterior |
| `d` / `→` | NAV_RIGHT | Dígito siguiente |
| `Enter` | Confirmar | Enviar PIN |
| `x` / `Esc` | Cancelar / back | Cancelar PIN entry |
| `h` | Abrir lista de dispositivos | — |
| `n` | Siguiente dispositivo | — |
| `p` | Dispositivo anterior | — |
| `q` | Salir | — |

*ScouterApp (celular — WebSocket):*

| Panel | Control | Acción |
|-------|---------|--------|
| BASE | D-pad ▲▼◄► + OK | Navegación + confirmar. ◀▶ = prev/next device en streaming |
| BASE | CANCEL / HOME / QR SCAN / URL | Botones de acción (lista vertical) |
| BASE | AUTH (fingerprint) | Auth biométrica real (FaceID/huella) — bypass PIN si OK |
| BASE | ◆ AI CHAT | Abre pantalla de chat AI |
| BASE | Swipe → borde izq | Abre NUMPAD full-screen |
| BASE | Swipe ← borde der | Abre ALPHA full-screen |
| NUMPAD | 0-9 + ⌫ + SEND | Entrada directa de dígitos (modo PIN) |
| NUMPAD | Swipe ← | Cierra numpad (no disponible en PIN mode) |
| ALPHA | QWERTY + SPACE + ENTER + ⌫ | Entrada de texto (shift toggle) |
| ALPHA | Swipe → | Cierra teclado |
| AI CHAT | TextField + SEND | Enviar mensaje al AI (stub: echo response) |
| AI CHAT | ✕ CLOSE | Cierra chat |

### PIN Auth Flow
**Estado:** Completado

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `software/scouterhud/auth/auth_manager.py` | AuthManager: PIN validation, rate limiting (5 attempts → 15 min lockout), PINs from config | Listo |
| `software/scouterhud/auth/pin_entry.py` | PinEntry: UI interactiva de 4 dígitos, render 240x240 | Listo |

**PINs de demo:** Cargados desde `emulator/config.yaml` (no hardcoded en código fuente).

| Device ID | PIN | Auth type |
|-----------|-----|-----------|
| `monitor-bed-12` | `1234` | pin |
| `press-machine-07` | `5678` | pin |
| `car-001` | — | open |
| `srv-prod-01` | — | token |
| `thermo-kitchen` | — | open |

**Flujo:** `--auth pin` → pantalla PIN → navegar dígitos con w/s (teclado) o numpad directo (app) → enter/SEND para enviar → si OK conecta, si no muestra error con intentos restantes → 5 fallos = lockout 15 min.

### Multi-device Switching
**Estado:** Completado

- [x] `ConnectionManager` mantiene historial de dispositivos conocidos
- [x] `switch_next()` / `switch_prev()` para rotar entre dispositivos
- [x] Pantalla `render_device_list()` con selección, scroll, indicador de activo
- [x] Integrado en state machine: `h` abre lista, `n`/`p` cambia directo

### Test End-to-End
**Estado:** Completado

- [x] Emulador publica datos realistas por MQTT
- [x] ScouterHUD se conecta, recibe metadata y renderiza datos en vivo
- [x] Verificado con `--preview` en WSL2 (PNG actualizado en tiempo real)
- [x] 6 layouts renderizan correctamente (medical, vehicle, infra, home, industrial, generic)
- [x] PIN auth flow funcional (pantalla PIN, validación, error/retry)
- [x] State machine: SCANNING → AUTH → CONNECTING → STREAMING → DEVICE_LIST → ERROR

**Layouts implementados:**

| Device Type | Layout | Campos principales |
|-------------|--------|--------------------|
| `medical.*` | Vitales grandes + alertas prominentes | SpO2, HR, Resp, Temp, alertas color-coded |
| `vehicle.*` | RPM + velocidad + gauges | RPM, km/h, Coolant, Fuel, Battery, DTC codes |
| `infra.*` | Dashboard métricas + costos | CPU%, MEM%, Disk%, Cost USD, instance ID |
| `home.*` | Temperatura + modo | Temp, Target, Humidity, Mode (heating/cooling/idle) |
| `industrial.*` | Presión grande + ciclos | Pressure bar, Temp, Cycle count, Status |
| `custom.*` | Key-value genérico | Cualquier campo JSON |

### Unit Tests
**Estado:** Completado

179 tests Python + 32 tests Flutter (211 total) cubriendo todos los módulos core. Python tests corren en <0.3s sin hardware ni broker.

```bash
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python -m pytest tests/ -v
```

| Test file | Tests | Cubre |
|-----------|-------|-------|
| `tests/test_protocol.py` | 23 | Parsing QR-Link URLs, DeviceLink, metadata update, fail-closed auth, URL length limit |
| `tests/test_auth.py` | 34 | AuthManager (PIN/token), PinEntry (UI logic, render, retry), rate limiting (lockout, per-device, reset) |
| `tests/test_renderer.py` | 15 | 6 layouts, status screens, device list, alertas, edge cases |
| `tests/test_input.py` | 13 | EventType, InputEvent, InputManager con mock backends |
| `tests/test_connection.py` | 11 | Device history, switching, dedup, mock MQTT transport |
| `tests/test_gauntlet.py` | 21 | Pad→event translation (nav + numeric), BLE notification parser, battery |
| `tests/test_phone_input.py` | 55 | PhoneInput: message parsing, event map, queue, state broadcast, biometric, device_list, input validation |
| `app/flutter/.../test/hud_state_test.dart` | 27 | Flutter: HUD state, panel state, chat messages, device list, DeviceInfo, updateLastAiMessage |
| `app/flutter/.../test/llm_service_test.dart` | 5 | Flutter: LlmService initial state, generate when not ready |

### BLE Gauntlet Input Stub
**Estado:** Completado (stub — necesita hardware ESP32 para test real)

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `software/scouterhud/input/gauntlet_input.py` | GauntletInput: BLE client con bleak, auto-scan, reconnect | Listo |

**Características:**
- Implementa `InputBackend` — se conecta al `InputManager` igual que keyboard
- Custom BLE GATT service con UUIDs definidos (matching gauntlet-tech-doc.md)
- Wire format: 4 bytes (event_type + pad_mask + timestamp_ms)
- Modo navegación: 5 pads → NAV_UP/DOWN/LEFT/RIGHT + CONFIRM
- Modo numérico: pads remap a DIGIT_UP/DOWN/NEXT/PREV/SUBMIT
- Gestos: chord PAD 1+4 → CANCEL, double-tap PAD 5 → HOME, hold PAD 5 → TOGGLE_VOICE
- API de feedback háptico: `send_haptic(HapticPattern.SHORT|DOUBLE|LONG|SUCCESS)`
- Monitoreo de batería del Gauntlet
- Background thread con asyncio: scan → connect → reconnect automático
- Graceful degradation: si `bleak` no está instalado, se deshabilita silenciosamente

**Dependencia opcional:** `pip install bleak` (no incluida en deps base, solo necesaria con hardware)

### Pendiente en Phase 1 (software — se puede hacer sin hardware)

- [ ] Test de memoria en Pi Zero 2W

### Pendiente en Phase 1 (hardware)

- [ ] Primer print 3D del housing óptico
- [ ] Soldar y testear Pi Zero 2W + ST7789
- [ ] Implementar `display/backend_spi.py` (ST7789 via SPI, lib: `st7789`)
- [ ] Test de latencia display render en Pi Zero
- [ ] *(Opcional)* Implementar `camera/backend_pi.py` (PiCamera, lib: `picamera2`) — solo si se usa módulo de cámara

---

## Phase A0 — ScouterApp: PoC WebSocket
**Estado:** Completado

- [x] WebSocket server en el HUD (`ws://localhost:8765`)
- [x] `PhoneInput` backend que recibe eventos por WebSocket → `InputManager`
- [x] Página HTML landscape con D-pad + modo numérico (PIN entry)
- [x] QR scanning desde la página web (BarcodeDetector API + input manual de URL)
- [x] Testear: abrir desde browser del celular → enviar qrlink URL → HUD se conecta
- [x] HUD broadcast de estado a phones conectados (SCANNING/AUTH/STREAMING/ERROR)
- [x] 47 tests nuevos (163 total)
- [x] Documentado en STATUS.md

**Criterio de éxito:** Abrir una página web en el celular → enviar una QR-Link URL → el HUD se conecta y muestra datos. **VERIFICADO.**

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `software/scouterhud/input/phone_input.py` | PhoneInput backend: WebSocket server + HTTP + digits + alpha + ai_chat + biometric | Listo |
| `app/web/index.html` | Página de control mobile: D-pad, modo PIN, QR scan, URL input, status bar | Listo |
| `software/tests/test_phone_input.py` | 47 tests: parsing, event map, queue, state broadcast | Listo |

### Cómo correr con control por celular

```bash
# Terminal 1: MQTT broker
docker run --rm -p 1883:1883 eclipse-mosquitto:2 mosquitto -c /mosquitto-no-auth.conf

# Terminal 2: Emulador de dispositivos
cd ~/scouterHUD/emulator && ../.venv/bin/python emulator.py

# Terminal 3: HUD con phone control
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python -m scouterhud.main --preview --phone

# Ver pantalla del Scouter
code /tmp/scouterhud_live.png

# Abrir control remoto en browser
# http://localhost:8765/        (mismo PC)
# http://<tu-ip>:8765/          (celular en misma WiFi)
```

### QR-Link URLs para probar desde el celular

| Dispositivo | URL | Auth |
|---|---|---|
| Auto OBD-II | `qrlink://v1/car-001/mqtt/localhost:1883?t=vehicles/car001/obd2` | open |
| Termostato | `qrlink://v1/thermo-kitchen/mqtt/localhost:1883?t=home/kitchen/climate` | open |
| Monitor respiratorio | `qrlink://v1/monitor-bed-12/mqtt/localhost:1883?auth=pin&t=ward3/bed12/vitals` | PIN: 1234 |
| Prensa industrial | `qrlink://v1/press-machine-07/mqtt/localhost:1883?auth=pin&t=factory/zone2/press07` | PIN: 5678 |
| Servidor AWS | `qrlink://v1/srv-prod-01/mqtt/localhost:1883?auth=token&t=infra/prod/server01` | token |

### Phase A1 — ScouterApp: Flutter MVP
**Estado:** v0.4.0 — Auth biométrica + device list

- [x] Flutter app con pantalla de control (D-pad + confirm + cancel)
- [x] **QR scanning nativo** (mobile_scanner 6.0.11 — cámara del celular)
- [x] Landscape mode forzado (immersive sticky)
- [x] WebSocket connection con auto-reconnect
- [x] Pantalla de conexión con IP:Port guardado en SharedPreferences
- [x] D-pad grande (80x68px) para navegación
- [x] Teclado numérico directo para PIN entry (digit_0..9, backspace, submit)
- [x] Cambio automático D-pad ↔ Numpad según modo del HUD
- [x] Botones de acción: CANCEL, HOME, QR SCAN, URL INPUT (lista vertical)
- [x] Margen derecho 48px + izquierdo 40px (zonas seguras: botones físicos + cámara)
- [x] Status bar 3 columnas: conexión | SCOUTERAPP + device | modo (REMOTE/NUMPAD/KEYBOARD/AI CHAT)
- [x] PIN banner visible cuando el HUD pide PIN
- [x] URL input manual (dialog para pegar qrlink:// URLs)
- [x] **Sistema de paneles full-screen** (BASE/NUMPAD/ALPHA/AI CHAT) — una pantalla a la vez
- [x] **Teclado QWERTY custom** (SPACE vertical izq, 3 filas QWERTY, ENTER vertical der, SHIFT, ⌫)
- [x] **Swipe gestures**: borde izq → NUMPAD, borde der → ALPHA, swipe inverso para cerrar
- [x] **AI Chat screen** (header púrpura, mensajes user/AI, TextField + SEND, stub backend)
- [x] **Botón fingerprint** (88x180px, icono + AUTH label, evento biometric_auth)
- [x] **Tema visual**: fondo navy #1A1A2E, colores por función (red=cancel, blue=home, yellow=numpad, green=confirm, orange=url, purple=AI, cyan=keyboard)
- [x] D-pad ◀▶ → prev/next device en streaming (Python backend, sin botones duplicados)
- [x] Protocolo WebSocket extendido: alpha_key (con value), alpha_backspace/enter/shift, ai_chat, ai_response, biometric_auth
- [x] 32 tests Flutter + 179 tests Python passing (211 total)
- [x] **Autenticación biométrica** (FaceID/huella vía `local_auth`) — bypass PIN cuando biometric OK
- [x] **AI Chat con LLM local** — Gemma 3 1B on-device via flutter_gemma. Streaming, GPU, sin cloud
- [x] **Pantalla device list** — lista de dispositivos con BACK, CONNECT, filas tocables; auto-switch desde HUD
- [ ] **AI Context awareness** — inyectar datos del HUD (sensores, alarmas) en el contexto del LLM
- [ ] Comunicación BLE con el HUD (actualmente usa WebSocket vía WiFi)
- [ ] Pairing flow (escanear QR del HUD)

> **AI/LLM (Feb 2026):** Inferencia local funcional con `flutter_gemma` v0.11.16 + Gemma 3 1B IT int4 (529 MB, descarga una vez desde GitHub Releases).
> Intentos anteriores fallidos: `llama_cpp_dart` (no funcionó), `flutter_llama` v1.1.2 (segfaults nativos en llama.cpp C++).
> **Requisito firme:** el LLM corre en el phone (no cloud, no LAN). Datos de salud son PII/PHI — compliance HIPAA/GDPR.

**APK releases:**

| Versión | Fecha | Cambios | Tamaño |
|---------|-------|---------|--------|
| v0.1.3 | 2026-02-17 | Primera versión funcional: WebSocket, QR scan, D-pad, PIN +/− | 67.9MB |
| v0.2.0 | 2026-02-17 | UI/UX: D-pad grande, numpad directo, márgenes, layout reorganizado | 67.9MB |
| v0.3.0 | 2026-02-20 | Panel system: QWERTY keyboard, AI Chat, fingerprint button, swipe gestures, dark navy theme | 68.5MB |
| v0.4.0 | 2026-02-20 | Auth biométrica (local_auth), device list screen con BACK/CONNECT/tap, 191 tests | 66MB |
| v0.4.0-gemma | 2026-02-24 | On-device AI (flutter_gemma + Gemma 3 1B), fallback model download, streaming chat, 211 tests | 220.7MB |

**Archivos Flutter:**

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `lib/main.dart` | Entry point: ScouterApp + ConnectScreen + auto-connect | Listo |
| `lib/screens/control_screen.dart` | Panel router: BASE/NUMPAD/ALPHA/AI_CHAT + swipe gestures + edge hints | Listo |
| `lib/screens/numpad_screen.dart` | Full-screen numpad con PIN banner (auto-open en PIN mode) | Listo |
| `lib/screens/alpha_keyboard_screen.dart` | Full-screen QWERTY keyboard con safe zones | Listo |
| `lib/screens/ai_chat_screen.dart` | Full-screen AI chat: local Gemma 3 1B inference, streaming tokens, download progress, model status indicator | Listo |
| `lib/screens/qr_scanner_screen.dart` | QR scanner con mobile_scanner + error handling | Listo |
| `lib/widgets/dpad_widget.dart` | D-pad 5 botones (80x68px) para navegación | Listo |
| `lib/widgets/numpad_widget.dart` | Teclado numérico 4x3 para PIN entry | Listo |
| `lib/widgets/alpha_keyboard_widget.dart` | QWERTY: SPACE(80px)+SHIFT izq, 3 filas centro, ENTER(80px) der, ⌫ en fila 3 | Listo |
| `lib/widgets/action_button_grid.dart` | Lista vertical: CANCEL, HOME, QR SCAN, URL | Listo |
| `lib/screens/device_list_screen.dart` | Pantalla device list: BACK, CONNECT, filas tocables, auto-switch | Listo |
| `lib/widgets/fingerprint_button.dart` | Auth biométrica real vía local_auth (FaceID/huella), estados visuales | Listo |
| `lib/widgets/ai_chat_button.dart` | Botón púrpura "◆ AI CHAT" debajo del D-pad | Listo |
| `lib/widgets/edge_hint_widget.dart` | Líneas verticales con label rotado (NUMPAD/ALPHA) | Listo |
| `lib/widgets/gesture_guide_bar.dart` | Barra inferior: "◁ NUMPAD" / "ALPHA ▷" | Listo |
| `lib/widgets/status_bar_widget.dart` | 3 columnas: conexión, titulo+device, modo activo | Listo |
| `lib/services/websocket_service.dart` | WebSocket client + sendAlphaKey + sendAiChat + sendBiometricAuth + device_list handler | Listo |
| `lib/services/llm_service.dart` | LlmService: flutter_gemma wrapper, model download (GitHub→HF fallback), streaming inference | Listo |
| `lib/models/hud_state.dart` | HudConnection: state, numericMode, activePanel, chatMessages, deviceList, DeviceInfo, updateLastAiMessage | Listo |
| `lib/models/panel_state.dart` | Enum: base, numpad, alpha, aiChat, deviceList | Listo |
| `lib/theme/scouter_colors.dart` | Constantes de color: background, surface, red..cyan, text, border | Listo |

**Build pipeline:**

```bash
# Build APK
cd ~/scouterHUD/app/flutter/scouter_app && ~/flutter/bin/flutter build apk --release

# Tests
cd ~/scouterHUD/app/flutter/scouter_app && ~/flutter/bin/flutter test

# APK output: build/app/outputs/flutter-apk/app-release.apk
```

**Configuración Android requerida:**

| Setting | Valor | Razón |
|---------|-------|-------|
| Kotlin | 2.1.0 | mobile_scanner 6.0.11 |
| AGP | 8.9.1 | flutter_gemma (androidx.core:core-ktx 1.17.0) |
| Gradle | 8.11.1 | AGP 8.9.1 |
| compileSdk | 36 | mobile_scanner |
| NDK | 27.0.12077973 | mobile_scanner + shared_preferences |
| minSdk | 24 | flutter_gemma (MediaPipe GenAI) |
| Java | 17 | Kotlin 2.1.0 |
| usesCleartextTraffic | true | ws:// (no TLS) en Android 9+ |

**Nota WSL2:** Si usas `networkingMode=mirrored` en `.wslconfig` (WSL2 moderno), los puertos de WSL se ven directamente desde la red — **no necesitas port proxy**. Si usas el modo NAT antiguo, necesitas port forwarding:
```powershell
# PowerShell como Admin (solo para NAT mode, NO necesario con mirrored)
netsh interface portproxy add v4tov4 listenport=8765 listenaddress=0.0.0.0 connectport=8765 connectaddress=127.0.0.1
New-NetFirewallRule -DisplayName "ScouterHUD WS" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
```

---

## Phase S0 — Security Quick Wins
**Estado:** Completado

Hardening de seguridad sin cambios de arquitectura. Ver [security-model.md](security-model.md) para el modelo completo.

- [x] **Eliminado "accept any PIN" fallback** — dispositivos sin PIN configurado son rechazados
- [x] **PINs removidos del código fuente** — cargados desde `emulator/config.yaml` via constructor
- [x] **Rate limiting de PIN** — 5 intentos fallidos → lockout 15 min por dispositivo
- [x] **Validación de input WebSocket** — mensajes >4KB rechazados, rate limit 30 msg/s por cliente
- [x] **Validación de URLs** — QR-Link URLs >512 chars rechazadas
- [x] **Validación de AI chat** — mensajes >1024 chars truncados
- [x] **Fail-closed para auth desconocido** — `?auth=foobar` rechaza la URL (antes defaulteaba a open)
- [x] **Security headers HTTP** — X-Frame-Options, CSP, X-Content-Type-Options, Referrer-Policy
- [x] 12 tests nuevos de seguridad (179 Python total)

| Archivo | Cambio |
|---------|--------|
| `software/scouterhud/auth/auth_manager.py` | Rate limiting, fail-closed, PINs por config |
| `software/scouterhud/main.py` | `_load_demo_pins()` desde emulator config |
| `software/scouterhud/input/phone_input.py` | Security headers, message size/rate limit, URL/chat validation |
| `software/scouterhud/qrlink/protocol.py` | URL length limit, fail-closed auth |

---

### Phase A2 — Tactile Overlay

- [ ] Diseño 3D del overlay para 2-3 tamaños de celular
- [ ] Prototipo con silicona de casteo + molde 3D
- [ ] Modo calibración en la app
- [ ] Validar con guantes de nitrilo

---

## Phase G0 — ScouterGauntlet: Proof of Concept (opcional)
**Estado:** Baja prioridad (accesorio opcional para casos extremos)

> **Nota:** Para el 90% de los usuarios, la ScouterApp es suficiente. El Gauntlet ESP32 es solo para:
> guantes gruesos (industrial, soldadura), ambientes mojados/IP67, o usuarios sin celular.

- [ ] ESP32-S3 dev board en breadboard
- [ ] 5 pads de cinta de cobre conectados a touch pins
- [ ] Firmware Arduino: detectar toques individuales y chords (<50ms latencia)
- [ ] BLE: enviar eventos a un celular (app BLE scanner para validar)
- [ ] Motor de vibración con MOSFET
- [ ] Medir consumo en deep sleep vs activo

### Phase G1 — Integración con ScouterHUD

- [ ] Custom BLE GATT service en el Gauntlet firmware
- [x] Módulo `input/gauntlet_input.py` en ScouterHUD (con `bleak`) — **stub completado**
- [x] Modo navegación: pad→event translation implementado y testeado
- [x] Modo numérico: pad remap implementado y testeado
- [x] API de feedback háptico: `send_haptic()` implementado
- [ ] Test end-to-end con hardware real (ESP32-S3 + ScouterHUD)

---

## Phase B0 — ScouterBridge: USB Serial MVP
**Estado:** Pendiente (esperando hardware)

- [ ] ESP32-S3 dev board con USB Host habilitado
- [ ] Leer datos seriales de un dispositivo USB (ej: Arduino enviando JSON)
- [ ] Parsear datos (JSON lines)
- [ ] Publicar por MQTT en formato QR-Link (mismos topics/formato que el emulador)
- [ ] Portal captive para WiFi + configuración básica
- [ ] Generar QR-Link code desde el portal
- [ ] LED de status

**Criterio de éxito:** Un Arduino enviando JSON por USB serial → Bridge publica por MQTT → ScouterHUD muestra datos con layout `custom.*`.

---

## Entorno de desarrollo

| Componente | Detalle |
|------------|---------|
| Python | 3.12 (venv en `.venv/`) |
| OS | Linux (WSL2) |
| Deps emulador | paho-mqtt 2.1, pyyaml 6.0, qrcode 8.2, reportlab 4.4, Pillow 12.1 |
| Deps software | pygame 2.x, pyzbar 0.1, paho-mqtt 2.1, Pillow 12.1, websockets 16.0 |
| Deps dev | pytest 9.x (`pip install -e ".[dev]"`) |
| Deps futuras | bleak (BLE), st7789 (SPI display), picamera2 (solo con módulo de cámara opcional) |
| Dep sistema | `libzbar0` (`sudo apt install libzbar0`), Docker |
| Firmware tools | PlatformIO (para ESP32 Gauntlet + Bridge) |

---

## Cómo correr el sistema completo (end-to-end)

Se necesitan **3 terminales**. Todas desde la raíz del proyecto (`~/scouterHUD`).

### Prerrequisitos (una sola vez)

```bash
# Instalar dependencia de sistema
sudo apt install libzbar0

# Crear venv e instalar dependencias
python3.12 -m venv .venv
cd emulator && ../.venv/bin/pip install -e . && cd ..
cd software && ../.venv/bin/pip install -e . && cd ..
```

### Terminal 1 — Broker MQTT

```bash
docker run --rm -p 1883:1883 eclipse-mosquitto:2 mosquitto -c /mosquitto-no-auth.conf
```

Dejar corriendo. Verás logs del broker cuando se conecten clientes.

### Terminal 2 — Emulador de dispositivos

```bash
cd ~/scouterHUD/emulator && ../.venv/bin/python emulator.py
```

Esto levanta los 5 dispositivos publicando datos por MQTT. Para un solo dispositivo:

```bash
cd ~/scouterHUD/emulator && ../.venv/bin/python emulator.py --device monitor-bed-12
```

### Terminal 3 — ScouterHUD (preview en WSL2)

```bash
# Opción A: Demo directo (teclado)
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python -m scouterhud.main \
    --preview --demo monitor-bed-12 --broker localhost:1883 --topic ward3/bed12/vitals

# Opción B: Phone control (celular como control remoto)
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python -m scouterhud.main --preview --phone

# Opción C: Demo + phone (ambos controles)
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python -m scouterhud.main \
    --preview --phone --demo monitor-bed-12 --broker localhost:1883 --topic ward3/bed12/vitals
```

Luego abrir `/tmp/scouterhud_live.png` en VSCode para ver el HUD en vivo (`code /tmp/scouterhud_live.png`).

Para phone control:
- **ScouterApp (recomendado):** Instalar APK en Android (`scouter-app-v0.4.0.apk`), ingresar `<tu-ip>:8765`
- **Web fallback:** Abrir `http://localhost:8765/` (o `http://<tu-ip>:8765/` desde celular en la misma WiFi)

**Controles en terminal (modo preview):** `w/a/s/d` = navegar, `enter` = confirmar, `x` = cancelar, `h` = lista de dispositivos, `n/p` = cambiar dispositivo, `q` = salir.

### Dispositivos disponibles para `--demo`

| Device ID | --topic | Auth | Tipo |
|-----------|---------|------|------|
| `monitor-bed-12` | `ward3/bed12/vitals` | pin (1234) | Monitor respiratorio |
| `car-001` | `vehicles/car001/obd2` | open | Vehículo OBD-II |
| `srv-prod-01` | `infra/prod/server01` | open | Servidor cloud |
| `thermo-kitchen` | `home/kitchen/climate` | open | Termostato |
| `press-machine-07` | `factory/zone2/press07` | pin (5678) | Prensa industrial |

### Probar PIN auth

```bash
# Dispositivo con PIN — aparece pantalla de ingreso de PIN
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python -m scouterhud.main \
    --preview --demo monitor-bed-12 --broker localhost:1883 --topic ward3/bed12/vitals --auth pin
```

1. Se muestra pantalla "PIN REQUIRED"
2. Usar `w`/`s` para cambiar dígito, `a`/`d` para mover cursor
3. Ingresar `1234` y presionar `enter`
4. Si el PIN es correcto → conecta y muestra datos
5. Si es incorrecto → muestra "Invalid PIN", permite reintentar
6. `x` para cancelar y volver a scanning

### Probar multi-device switching

```bash
# 1. Conectar al primer dispositivo
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python -m scouterhud.main \
    --preview --demo monitor-bed-12 --broker localhost:1883 --topic ward3/bed12/vitals

# Mientras está corriendo y mostrando datos:
#   h → abre lista de dispositivos (por ahora solo 1)
#   n → cambia al siguiente dispositivo conocido
#   p → cambia al anterior
#   x → desconecta y vuelve a scanning
```

Nota: para tener múltiples dispositivos en la lista, habría que escanear varios QR o conectar a varios --demo secuencialmente. En el futuro la ScouterApp permitirá navegar la lista con swipe.

### Generar QR codes

```bash
cd ~/scouterHUD/emulator && ../.venv/bin/python generate_all_qrs.py
# Salida: emulator/qr_output/*.png + emulator/qr_output/all_qrcodes.pdf
```

### Escanear QR desde archivo (en lugar de --demo)

```bash
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python -m scouterhud.main \
    --preview --scan ../emulator/qr_output/monitor-bed-12.png
```
