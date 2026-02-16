# ScouterBridge — Universal Device-to-QR-Link Adapter

## Technical Design Document v0.1

**Project Codename:** ScouterBridge  
**Companion to:** ScouterHUD + QR-Link Protocol  
**Author:** Ger  
**Date:** February 2026  
**License:** MIT (Software) / CERN-OHL-S v2 (Hardware)  
**Status:** Concepto / Diseño

---

## 1. Vision & Scope

### 1.1 El problema del huevo y la gallina

QR-Link es un protocolo nuevo. Ningún dispositivo existente lo habla. Para que el ScouterHUD sea útil en el mundo real, necesitamos una de dos cosas:

- **Opción A:** Convencer a fabricantes de que adopten QR-Link → lento, años, requiere masa crítica
- **Opción B:** Crear un adaptador que conecte dispositivos legacy al ecosistema QR-Link → inmediato, nosotros lo controlamos

ScouterBridge es la Opción B.

### 1.2 Qué es ScouterBridge

Un dongle basado en ESP32-S3 que se conecta a cualquier dispositivo existente (via USB, UART serial, OBD-II, GPIO, o Bluetooth), lee sus datos nativos, los traduce al formato QR-Link, y los publica por WiFi/MQTT. Incluye un QR code adhesivo que apunta al bridge.

Es el equivalente de un Chromecast para QR-Link: en vez de esperar que el TV tenga streaming integrado, enchufás el dongle y listo.

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  DISPOSITIVO │  USB/   │ SCOUTER      │  WiFi/  │  SCOUTER     │
│  LEGACY      │──UART──►│ BRIDGE       │──MQTT──►│  HUD         │
│              │  OBD-II │ (ESP32-S3)   │         │              │
│  (monitor,   │  BLE    │              │         │  escanea QR  │
│   auto,      │  GPIO   │  traduce     │         │  del bridge  │
│   sensor,    │         │  protocolo   │         │  y ve datos  │
│   servidor)  │         │  legacy →    │         │  en vivo     │
│              │         │  QR-Link     │         │              │
└──────────────┘         └──────────────┘         └──────────────┘
                          ↑
                     [QR Code adhesivo]
                     pegado en el bridge
                     o en el dispositivo
```

### 1.3 Qué NO es

- No modifica el dispositivo original (no-invasivo)
- No reemplaza la interfaz original del dispositivo
- No requiere acceso al firmware del dispositivo
- No es un hub IoT genérico — está optimizado para QR-Link

### 1.4 La jugada estratégica

```
FASE 1 (ahora):     Bridge como producto → adopción del ecosistema
FASE 2 (tracción):  Fabricantes ven el valor → integran QR-Link nativo
FASE 3 (estándar):  QR-Link se vuelve estándar → bridge innecesario
                     pero ya tenemos comunidad, marca, y protocolo
```

Esto es exactamente el playbook de Chromecast (bridge → Cast protocol nativo en TVs), Bluetooth audio adapters (dongle → integración nativa), y USB WiFi adapters (dongle → WiFi integrado en todo).

Incluso si QR-Link se vuelve estándar y los bridges ya no son necesarios, el valor está en ser los dueños del protocolo y la comunidad.

---

## 2. Hardware

### 2.1 Selección del MCU: ESP32-S3

El ESP32-S3 es ideal para este uso porque:

- **USB OTG nativo:** Puede actuar como USB Host para leer dispositivos USB (serial adapters, OBD-II readers, etc.) sin chip externo
- **WiFi + BLE 5.0:** Publica por MQTT sobre WiFi y puede leer dispositivos BLE
- **UART × 3:** Tres puertos serial de hardware para conectar dispositivos legacy
- **10 touch capacitivos:** Podríamos agregar botones de config sin partes extra
- **Flash suficiente:** 4-8MB para firmware + plugins de protocolo
- **Costo:** ~$3-5 el módulo

### 2.2 Form factors

El bridge tiene diferentes "sabores" según el tipo de conexión al dispositivo:

**Bridge USB (universal):**
```
┌─────────────────────────────────┐
│      ScouterBridge USB          │
│                                 │
│  [USB-A male] ←→ [ESP32-S3]    │
│  (al dispositivo)  │           │
│                    WiFi         │
│                    antenna      │
│                                 │
│  [USB-C female]  [LED] [QR]    │
│  (power/config)        sticker │
│                                 │
│  Tamaño: ~50x25x12mm           │
│  (similar a un USB flash drive) │
└─────────────────────────────────┘
```

**Bridge OBD-II (vehículos):**
```
┌─────────────────────────────────┐
│      ScouterBridge OBD-II       │
│                                 │
│  [OBD-II connector] ←→ [ESP32] │
│  (plug directo al    │         │
│   puerto del auto)   WiFi      │
│                                 │
│  [LED status]  [QR sticker]    │
│                                 │
│  Alimentación: 12V del OBD-II  │
│  Tamaño: ~60x40x20mm           │
└─────────────────────────────────┘
```

**Bridge Serial/GPIO (industrial/maker):**
```
┌─────────────────────────────────┐
│      ScouterBridge Serial       │
│                                 │
│  [Screw terminals] ←→ [ESP32]  │
│   TX/RX/GND/5V       │        │
│   + 4x GPIO           WiFi    │
│                                 │
│  [USB-C]  [LED]  [QR sticker] │
│  (power/config)                │
│                                 │
│  Tamaño: ~55x30x15mm           │
│  Ideal para sensores, PLCs     │
└─────────────────────────────────┘
```

**Bridge BLE (dispositivos Bluetooth):**
```
┌─────────────────────────────────┐
│      ScouterBridge BLE          │
│                                 │
│  [Antena BLE] ←→ [ESP32-S3]   │
│  (escanea y conecta  │        │
│   dispositivos BLE)   WiFi    │
│                                 │
│  [USB-C]  [LED]  [QR sticker] │
│  (power)                       │
│                                 │
│  Lee: fitness bands, sensores  │
│  BLE, medical BLE devices      │
└─────────────────────────────────┘
```

### 2.3 BOM — Bridge USB (MVP)

| # | Componente | Modelo | Precio |
|---|-----------|--------|--------|
| 1 | MCU | ESP32-S3 Mini (N4R2, USB OTG) | $3-5 |
| 2 | Regulador | AMS1117-3.3 (5V→3.3V) | $0.10 |
| 3 | Conector USB-A | Male, para conectar al dispositivo | $0.20 |
| 4 | Conector USB-C | Female, para power/config | $0.30 |
| 5 | LED | RGB o bicolor (status) | $0.10 |
| 6 | Antena | PCB antenna (integrada en módulo) | — |
| 7 | Capacitores/resistencias | Bypass, pull-ups | $0.30 |
| 8 | PCB | 2-layer, JLCPCB | $1-2 |
| 9 | Enclosure | 3D printed o moldeo | $1-2 |
| 10 | QR Sticker | Impreso, adhesivo | $0.10 |

**Costo total estimado (Bridge USB):** $6-10 USD

### 2.4 BOM — Bridge OBD-II

| # | Componente | Modelo | Precio |
|---|-----------|--------|--------|
| 1 | MCU | ESP32-S3 Mini | $3-5 |
| 2 | OBD-II transceiver | MCP2515 (CAN) + MCP2551 (driver) | $2-3 |
| 3 | Regulador | LM2596 (12V→3.3V, del auto) | $1 |
| 4 | Conector OBD-II | Male DB16 | $2-3 |
| 5 | PCB + enclosure | Custom | $2-3 |

**Costo total estimado (Bridge OBD-II):** $10-15 USD

---

## 3. Arquitectura de software

### 3.1 Concepto: Plugin-based protocol translation

El firmware del bridge tiene una arquitectura de plugins. Cada plugin sabe cómo "hablar" un protocolo legacy y traducirlo a datos QR-Link.

```
┌─────────────────────────────────────────────────────┐
│                 SCOUTERBRIDGE FIRMWARE               │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │              PLUGIN MANAGER                     │  │
│  │  Carga el plugin correcto según configuración   │  │
│  └──────────────┬─────────────────────────────────┘  │
│        ┌────────┼────────┬──────────┬──────────┐     │
│  ┌─────▼────┐ ┌─▼──────┐ ┌▼────────┐ ┌▼───────┐    │
│  │ USB      │ │OBD-II  │ │Modbus   │ │BLE     │    │
│  │ Serial   │ │(CAN)   │ │RTU      │ │GATT    │    │
│  │ Plugin   │ │Plugin  │ │Plugin   │ │Plugin  │    │
│  │          │ │        │ │         │ │        │    │
│  │ Lee:     │ │Lee:    │ │Lee:     │ │Lee:    │    │
│  │ CDC/ACM  │ │PIDs    │ │Registers│ │Charact.│    │
│  │ FTDI     │ │DTCs    │ │Coils    │ │Services│    │
│  │ CP210x   │ │        │ │         │ │        │    │
│  └────┬─────┘ └───┬────┘ └────┬────┘ └───┬────┘    │
│       └───────────┼──────────┼──────────┘          │
│              ┌────▼──────────▼────┐                  │
│              │  DATA NORMALIZER   │                  │
│              │  Transforma datos  │                  │
│              │  legacy → JSON     │                  │
│              │  QR-Link format    │                  │
│              └────────┬───────────┘                  │
│              ┌────────▼───────────┐                  │
│              │  MQTT PUBLISHER    │                  │
│              │  Publica en       │                  │
│              │  broker WiFi      │                  │
│              └────────────────────┘                  │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │  CONFIG / WEB UI                             │    │
│  │  Portal captive para setup WiFi + plugin     │    │
│  └─────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

### 3.2 Plugins previstos

| Plugin | Input | Output QR-Link type | Prioridad |
|--------|-------|---------------------|-----------|
| `usb_serial_generic` | USB CDC/FTDI/CP210x → líneas de texto | `custom.*` (configurable) | MVP |
| `obd2_can` | CAN bus via MCP2515 → PIDs estándar | `vehicle.obd2` | MVP |
| `modbus_rtu` | UART Modbus RTU → registers | `industrial.*` | Post-MVP |
| `ble_gatt_generic` | BLE GATT characteristics | `custom.*` | Post-MVP |
| `ble_medical` | BLE Health profiles (HR, SpO2, BP) | `medical.*` | Post-MVP |
| `gpio_analog` | GPIO digital + ADC analog reads | `custom.sensor` | Post-MVP |
| `http_scraper` | HTTP GET/JSON de APIs locales | `custom.*` | Post-MVP |
| `mqtt_bridge` | Rebroker MQTT legacy → QR-Link format | `custom.*` | Post-MVP |
| `snmp` | SNMP queries a switches/routers | `infra.network_switch` | Futuro |

### 3.3 Configuración via portal web captivo

Al primer encendido (o cuando no tiene WiFi configurado), el bridge crea un AP WiFi:

```
SSID: ScouterBridge-XXXX (últimos 4 del MAC)
Pass: scouterhud

Portal web en: http://192.168.4.1
```

**Pantallas del portal:**

1. **WiFi Setup:** Seleccionar red WiFi + password
2. **MQTT Setup:** Broker host:port (default: auto-discovery via mDNS)
3. **Plugin Selection:** Elegir qué plugin activar
4. **Plugin Config:** Configuración específica del plugin:
   - USB Serial: baud rate, parser (JSON lines, CSV, regex)
   - OBD-II: PIDs a leer, frecuencia
   - Modbus: slave address, registers, data types
   - BLE: MAC/service UUID del dispositivo target
5. **Device Identity:** Nombre, tipo QR-Link, icono, auth level
6. **QR Code:** Genera y muestra el QR para imprimir/pegar
7. **Live Preview:** Muestra los datos que está leyendo en tiempo real

### 3.4 Flujo de setup completo

```
1. UNBOX
   Usuario saca el bridge de la caja.

2. CONNECT
   Conecta el bridge al dispositivo legacy.
   (USB al puerto del monitor, OBD-II al auto, etc.)
   Alimenta el bridge (USB-C o del dispositivo mismo).

3. CONFIGURE
   Conecta su celular al WiFi "ScouterBridge-XXXX".
   Abre el portal web en el browser.
   Selecciona WiFi de la red local.
   Selecciona plugin (auto-detected si es posible).
   Configura parámetros del plugin.
   Define nombre y tipo del dispositivo.

4. GENERATE QR
   El portal genera el QR-Link code.
   Usuario lo imprime o lo muestra en pantalla.
   Lo pega como sticker en el dispositivo o en el bridge.

5. USE
   Con el ScouterHUD, escanea el QR.
   El HUD se conecta al bridge via MQTT.
   Ve los datos del dispositivo legacy en vivo.
   Todo funciona como si el dispositivo hablara QR-Link nativo.
```

### 3.5 Auto-discovery de protocolo

Cuando se conecta un dispositivo USB, el bridge puede intentar detectar automáticamente:

```
USB device conectado
    │
    ├─ Enumerar USB descriptors
    │   ├─ VID/PID conocido → sugerir plugin
    │   │   (ej: VID=0403 → FTDI serial device)
    │   │   (ej: VID=0BDA → OBD-II adapter)
    │   └─ CDC ACM class → generic serial
    │
    ├─ Si serial: probar parsers
    │   ├─ JSON lines? → auto-map fields
    │   ├─ CSV? → auto-detect columns
    │   ├─ NMEA? → GPS plugin
    │   └─ Unknown → raw text, user configures regex
    │
    └─ Si no USB: check UART
        ├─ Auto-baud detection (common rates)
        └─ Try Modbus RTU probe
```

---

## 4. Estructura del repositorio

```
scouterhud/
├── ... (HUD files) ...
├── gauntlet/
│   └── ... (Gauntlet files) ...
├── bridge/
│   ├── README.md
│   ├── firmware/
│   │   ├── platformio.ini
│   │   ├── src/
│   │   │   ├── main.cpp              → Setup + main loop
│   │   │   ├── config.h              → Pin definitions, defaults
│   │   │   │
│   │   │   ├── core/
│   │   │   │   ├── plugin_manager.h   → Plugin lifecycle management
│   │   │   │   ├── plugin_manager.cpp
│   │   │   │   ├── data_normalizer.h  → Legacy data → QR-Link JSON
│   │   │   │   ├── data_normalizer.cpp
│   │   │   │   ├── mqtt_publisher.h   → MQTT client + publish
│   │   │   │   ├── mqtt_publisher.cpp
│   │   │   │   ├── qrlink_meta.h      → QR-Link metadata + $meta topic
│   │   │   │   └── qrlink_meta.cpp
│   │   │   │
│   │   │   ├── plugins/
│   │   │   │   ├── base_plugin.h      → ABC for all plugins
│   │   │   │   ├── usb_serial.h       → USB serial reader (CDC/FTDI/CP210x)
│   │   │   │   ├── usb_serial.cpp
│   │   │   │   ├── obd2_can.h         → OBD-II via CAN bus
│   │   │   │   ├── obd2_can.cpp
│   │   │   │   ├── modbus_rtu.h       → Modbus RTU via UART
│   │   │   │   ├── modbus_rtu.cpp
│   │   │   │   ├── ble_gatt.h         → BLE GATT generic reader
│   │   │   │   ├── ble_gatt.cpp
│   │   │   │   ├── gpio_analog.h      → GPIO + ADC reader
│   │   │   │   └── gpio_analog.cpp
│   │   │   │
│   │   │   ├── web/
│   │   │   │   ├── captive_portal.h   → WiFi AP + DNS + HTTP server
│   │   │   │   ├── captive_portal.cpp
│   │   │   │   ├── web_ui.h           → Config web interface
│   │   │   │   ├── web_ui.cpp
│   │   │   │   └── static/            → HTML/CSS/JS for web UI
│   │   │   │       ├── index.html
│   │   │   │       ├── setup.html
│   │   │   │       └── style.css
│   │   │   │
│   │   │   ├── network/
│   │   │   │   ├── wifi_manager.h     → WiFi STA connect + reconnect
│   │   │   │   ├── wifi_manager.cpp
│   │   │   │   ├── mdns_discovery.h   → mDNS for MQTT broker discovery
│   │   │   │   └── mdns_discovery.cpp
│   │   │   │
│   │   │   └── utils/
│   │   │       ├── led_status.h       → LED patterns for status
│   │   │       ├── led_status.cpp
│   │   │       ├── ota_updater.h      → OTA firmware updates
│   │   │       └── ota_updater.cpp
│   │   │
│   │   └── test/
│   │       ├── test_normalizer.cpp
│   │       └── test_plugins.cpp
│   │
│   ├── hardware/
│   │   ├── 3d-models/
│   │   │   ├── bridge_usb_case.stl
│   │   │   ├── bridge_obd2_case.stl
│   │   │   └── bridge_serial_case.stl
│   │   ├── pcb/                        → KiCad files
│   │   │   ├── bridge_usb.kicad_pro
│   │   │   ├── bridge_obd2.kicad_pro
│   │   │   └── bridge_serial.kicad_pro
│   │   └── schematics/
│   │       ├── bridge_usb_schematic.svg
│   │       └── bridge_obd2_schematic.svg
│   │
│   └── docs/
│       ├── BUILD_GUIDE.md
│       ├── PLUGIN_DEVELOPMENT.md       → Cómo crear plugins custom
│       ├── SUPPORTED_DEVICES.md        → Lista de dispositivos probados
│       └── SETUP_GUIDE.md              → Guía de configuración
```

---

## 5. Plugin Development Kit

### 5.1 Plugin base interface

Cada plugin implementa una interfaz simple:

```cpp
// Pseudocode de la interfaz base

class BasePlugin {
public:
    // Metadata
    virtual const char* getName() = 0;        // "USB Serial"
    virtual const char* getVersion() = 0;     // "1.0.0"
    virtual const char* getDeviceType() = 0;  // "custom.serial"

    // Lifecycle
    virtual bool init(JsonObject config) = 0; // Setup con config del portal
    virtual void loop() = 0;                  // Llamado en main loop
    virtual void stop() = 0;                  // Cleanup

    // Data
    virtual JsonObject readData() = 0;        // Lee datos del dispositivo
    virtual int getRefreshMs() = 0;           // Frecuencia de lectura

    // Config UI (optional)
    virtual String getConfigHTML() = 0;       // HTML for web portal config
    virtual bool applyConfig(JsonObject) = 0; // Apply config from portal
};
```

### 5.2 Crear un plugin custom

La documentación `PLUGIN_DEVELOPMENT.md` guía a la comunidad para crear plugins para dispositivos específicos. El flujo:

1. Heredar de `BasePlugin`
2. Implementar `init()` con la conexión al dispositivo
3. Implementar `readData()` que retorna JSON con los datos
4. Definir el `deviceType` para que el HUD sepa qué layout usar
5. (Opcional) Implementar `getConfigHTML()` para parámetros en el portal
6. Compilar, flashear, testear
7. Hacer PR al repo

**Esto es lo que crea comunidad:** Cuando alguien necesita conectar un dispositivo específico (ej: una estación meteorológica Davis Vantage, o un monitor de glucosa Dexcom), escribe un plugin y lo comparte. El ecosistema crece orgánicamente.

---

## 6. Escenarios de uso concretos

### 6.1 Auto — OBD-II Bridge

```
[Puerto OBD-II del auto] ──CAN bus──► [ScouterBridge OBD-II]
                                            │
                                       WiFi/MQTT
                                            │
                                       [ScouterHUD]
                                       Ve: RPM, velocidad,
                                       temp motor, fuel,
                                       códigos de error
```

**Setup:** Enchufar bridge al OBD-II, configurar WiFi del auto/hotspot del celular, pegar QR en el dashboard.

### 6.2 Monitor médico — USB Serial Bridge

```
[Monitor de signos vitales] ──USB serial──► [ScouterBridge USB]
 (muchos monitores tienen                       │
  puerto serial/USB para                    WiFi/MQTT
  exportar datos)                                │
                                            [ScouterHUD]
                                            Ve: SpO2, HR,
                                            resp rate, temp,
                                            alertas
```

**Setup:** Conectar bridge al puerto serial/USB del monitor. Configurar parser para el formato del monitor (HL7, CSV, propietario). Pegar QR en el monitor.

### 6.3 Servidor/switch — SNMP/HTTP Bridge

```
[Switch de red] ──SNMP──► [ScouterBridge]
   o                           │
[API del servidor] ──HTTP──►   │
                          WiFi/MQTT
                               │
                          [ScouterHUD]
                          Ve: CPU, mem, disk,
                          port status, traffic,
                          costos cloud
```

**Setup:** Configurar IP del target, SNMP community o API endpoint. Bridge hace polling y publica.

### 6.4 Sensor industrial — Modbus RTU Bridge

```
[PLC / Sensor] ──RS-485──► [ScouterBridge Serial]
 (Modbus RTU)                    │
                            WiFi/MQTT
                                 │
                            [ScouterHUD]
                            Ve: presión, temp,
                            ciclos, alertas
```

**Setup:** Configurar slave address, registers a leer, data types (int16, float32), nombres de campos.

### 6.5 Dispositivo BLE — Fitness/Medical Bridge

```
[Pulse oximeter BLE] ──BLE──► [ScouterBridge BLE]
[Heart rate band]                    │
[Glucose monitor]               WiFi/MQTT
                                     │
                                [ScouterHUD]
                                Ve: HR, SpO2,
                                glucose, etc.
```

**Setup:** Escanear dispositivos BLE cercanos desde el portal, seleccionar, mapear characteristics a campos.

---

## 7. Roadmap

### Phase B0 — USB Serial Bridge MVP (Semana 1-3)

- [ ] ESP32-S3 dev board con USB Host habilitado
- [ ] Leer datos seriales de un dispositivo USB (ej: Arduino enviando JSON)
- [ ] Parsear datos (JSON lines)
- [ ] Publicar por MQTT en formato QR-Link
- [ ] Portal captive para WiFi + configuración básica
- [ ] Generar QR-Link code desde el portal
- [ ] LED de status (rojo=sin WiFi, verde=publicando)

### Phase B1 — OBD-II Bridge (Semana 4-6)

- [ ] Integrar MCP2515 + MCP2551 para CAN bus
- [ ] Plugin OBD-II: leer PIDs estándar (RPM, speed, temp, fuel, DTCs)
- [ ] Alimentación desde 12V del OBD-II port
- [ ] PCB custom para bridge OBD-II
- [ ] Enclosure impreso 3D

### Phase B2 — Portal web completo (Semana 7-8)

- [ ] Web UI con todas las pantallas de config
- [ ] Auto-discovery de protocolo USB
- [ ] Live preview de datos en el portal
- [ ] OTA firmware updates
- [ ] mDNS discovery del MQTT broker

### Phase B3 — Plugins adicionales (Semana 9-12)

- [ ] Plugin Modbus RTU
- [ ] Plugin BLE GATT genérico
- [ ] Plugin GPIO/ADC
- [ ] Plugin HTTP scraper
- [ ] Documentación PLUGIN_DEVELOPMENT.md
- [ ] SUPPORTED_DEVICES.md con lista de dispositivos probados

### Phase B4 — PCBs + enclosures finales (Semana 13+)

- [ ] PCB Bridge USB (KiCad → JLCPCB)
- [ ] PCB Bridge Serial
- [ ] Enclosures finales impresos 3D
- [ ] Testing de producción

---

## 8. Modelo de negocio potencial

### 8.1 Open source + hardware sales

El software y diseños son open source. Cualquiera puede construir su propio bridge. Pero la mayoría de la gente prefiere comprar uno armado.

| Producto | Costo | Precio venta | Margen |
|----------|-------|-------------|--------|
| Bridge USB (armado) | $8 | $25-30 | ~70% |
| Bridge OBD-II (armado) | $13 | $35-40 | ~65% |
| Bridge Serial (armado) | $10 | $30-35 | ~67% |
| Bridge BLE (armado) | $7 | $25-30 | ~72% |

### 8.2 Plugin marketplace (futuro)

Si el ecosistema crece, plugins premium para dispositivos específicos (ej: plugin para Siemens S7 PLC, o para Phillips patient monitors) podrían tener valor. Modelo freemium: plugins genéricos gratis, plugins especializados con soporte a $5-10.

### 8.3 QR-Link certification (futuro lejano)

Si QR-Link se vuelve estándar de facto, ofrecer certificación "QR-Link Compatible" a fabricantes de dispositivos. Similar a "Works with Alexa" o "Made for iPhone".

---

## 9. Ecosistema ScouterHUD completo

```
┌──────────────────────────────────────────────────────────┐
│                   ECOSISTEMA SCOUTERHUD                   │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ ScouterHUD  │  │ScouterGauntlet│ │ ScouterBridge  │  │
│  │             │  │              │  │                │  │
│  │ HUD display │  │ Input device │  │ Protocol       │  │
│  │ + camera    │  │ wrist pads   │  │ translator     │  │
│  │ + audio     │  │ BLE → HUD    │  │ legacy→QR-Link │  │
│  │ + AI agent  │  │              │  │                │  │
│  │ ~$55 USD    │  │ ~$15 USD     │  │ ~$8-15 USD     │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         │                │                   │           │
│         │          BLE   │                   │ WiFi/MQTT │
│         │◄───────────────┘                   │           │
│         │                                    │           │
│         │◄───────────────────────────────────┘           │
│         │         QR-Link Protocol                       │
│         │                                                │
│  ┌──────▼──────────────────────────────────────────┐     │
│  │              QR-LINK PROTOCOL                    │    │
│  │                                                  │    │
│  │  Dispositivos nativos (futuro)                   │    │
│  │  + Dispositivos legacy via Bridge (ahora)        │    │
│  │  + Emulador para desarrollo/testing              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  Stack completo: ~$78-85 USD                             │
│  Solo HUD + Bridge: ~$63-70 USD                          │
│  Solo HUD: ~$55 USD                                      │
└──────────────────────────────────────────────────────────┘
```

---

## 10. Referencias

### Proyectos de referencia
- **ESP32-UART-Bridge** (zvldz) — Bridge universal UART-to-WiFi, multi-protocolo
- **ESP USB Bridge** (Espressif) — USB Host/Device bridge oficial
- **esp32-usb-serial** (luc-github) — Arduino library para USB OTG Host
- **ESP32-S3-USB-OTG** — Dev board de referencia con USB Host + Device

### Hardware
- ESP32-S3 USB OTG Documentation (Espressif)
- MCP2515 CAN Controller Datasheet
- MCP2551 CAN Transceiver Datasheet
- ELM327 OBD-II Protocol Reference

### Protocolos legacy
- OBD-II PID Reference (SAE J1979)
- Modbus RTU Specification
- HL7 v2 (medical device communication)
- BLE GATT Health Profiles (Heart Rate, Pulse Oximeter, etc.)
- SNMP v2c/v3 Protocol
