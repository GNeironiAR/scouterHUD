# ScouterBridge OBD-II — Guia de Implementacion

**Fecha:** 2026-03-09
**Hardware:** ESP32-S3 SuperMini + ELM327 BT (Demo v1) o MCP2515 TJA1050 (Demo v2)
**Objetivo:** Reemplazar el emulador `car-001` con datos reales del auto

---

## 1. Que estamos construyendo

Un Bridge OBD-II real que lee datos del auto y los publica por **WiFi/MQTT** en formato QR-Link. El HUD ya tiene el layout `vehicle.obd2` funcionando — solo necesitamos que el Bridge publique en el mismo formato JSON que el emulador.

### Dos caminos de implementacion

**Demo v1 — OBD-II Scanner via BLE (recomendado primero):**
- Usa el scanner FNIRSI FD10 (BLE 5.1, comprado 2026-03-09)
- ESP32-S3 se conecta al FD10 por BLE (GATT characteristics)
- Zero cableado al auto — el scanner se enchufa al OBD-II port
- Latencia ~300-500ms (AT command round-trip via BLE UART)

**Demo v2 — MCP2515 CAN directo (después):**
- ESP32-S3 + MCP2515/TJA1050 lee CAN bus directamente
- Requiere pigtail OBD-II + cableado SPI
- Latencia ~50ms (CAN frames raw)
- No depende del ELM327

```
Demo v1 (FNIRSI FD10 BLE):

[Auto OBD-II port]                [FNIRSI FD10]          [ESP32-S3 SuperMini]
       |                                |                        |
    physical                        BLE 5.1                WiFi / MQTT
       |                                |                        |
       └──── enchufado ────────────────►└────── wireless ───────►└────► [Broker MQTT]
                                                                            |
                                                                 +---------+---------+
                                                                 |                   |
                                                            [Pi Zero 2W]      [ScouterApp]
                                                            HUD display       AI + control

Demo v2 (MCP2515 directo):

[Auto OBD-II port]
        |
    CAN bus (500 kbps)
        |
[MCP2515 + TJA1050] --- SPI ---> [ESP32-S3 SuperMini]
                                        |
                                   WiFi / MQTT
                                        |
                                   [Broker MQTT]
                                        |
                            +-----------+-----------+
                            |                       |
                       [Pi Zero 2W]          [ScouterApp]
                       HUD display           AI + control
```

> **IMPORTANTE:** Ambos demos usan **WiFi/MQTT** para Bridge→Broker→HUD (no BLE GATT).
> El doc anterior (`scouterbridge-demo-v1(1).md`) planteaba BLE para Bridge→HUD,
> pero el ecosistema actual usa MQTT. Eso simplifica: el HUD no sabe ni le importa
> si los datos vienen del emulador, del ELM327, o del MCP2515.

### Que cambia vs el emulador

| Aspecto | Emulador (hoy) | Bridge OBD-II (objetivo) |
|---------|----------------|--------------------------|
| Origen datos | Generados con SignalGenerator en Python | Leidos del CAN bus real del auto |
| Donde corre | PC (Python) | ESP32-S3 (C++ / Arduino) |
| Topic MQTT | `vehicles/car001/obd2` | `vehicles/car001/obd2` (mismo) |
| Formato JSON | `{rpm, speed_kmh, coolant_temp_c, fuel_pct, battery_v, dtc_codes}` | Identico |
| `$meta` topic | `vehicles/car001/obd2/$meta` (retained) | Identico |
| QR-Link URL | `qrlink://v1/car-001/mqtt/{broker}:1883?t=vehicles/car001/obd2` | Identico |

**El HUD no sabe ni le importa si los datos vienen del emulador o del Bridge.** Mismo topic, mismo JSON, mismo QR. Eso es el poder del protocolo.

---

## 2. Materiales (ya los tenemos)

### Demo v1 — Scanner BLE (sin cableado extra)

| # | Componente | Modelo exacto | Estado |
|---|-----------|---------------|--------|
| 1 | MCU | ESP32-S3 SuperMini HW-747 (Type-C, WiFi+BLE, 4MB Flash) | Tenemos x5 |
| 2 | Scanner OBD-II | FNIRSI FD10 (Bluetooth 5.1 BLE, ELM327 compatible) | Comprado 2026-03-09 |
| 3 | Cable USB-C | Para flashear ESP32 | Ya lo tenemos |

### Demo v2 — MCP2515 directo (materiales adicionales)

| # | Componente | Modelo exacto | Estado |
|---|-----------|---------------|--------|
| 1 | CAN controller | MCP2515 + TJA1050 module HW-184 (SPI, 8MHz crystal) | Tenemos x5 |
| 2 | Cable OBD-II | Tuxihapp J1962 16-pin pigtail (30cm, open wires) | Tenemos x1 |
| 3 | Cables | Dupont jumper wires (para breadboard) | Necesario |
| 4 | Breadboard | Para prototipo (no soldar aun) | Necesario |

### Scanner OBD-II — Especificaciones (verificadas 2026-03-11)

- **Modelo:** FNIRSI FD10
- **Firmware:** V2.1.2 (ELM327 v2.1 compatible)
- **Conectividad:** Bluetooth 5.1 (**BLE**, no BT Classic)
- **BLE device name:** `OBDII`
- **MAC address:** `50:88:06:D9:14:22`
- **Tension de trabajo:** 8V – 28V DC
- **App oficial:** YMOBD v2.9.3 (Android / iOS)
- **Vehiculo de prueba:** Honda CR-V 2010
- **Protocolo detectado:** ISO 15765-4 CAN 29-bit/500 kbps (extended frame IDs)
- **PIDs confirmados funcionando:** RPM, velocidad, temperatura refrigerante, tension bateria, carga motor, MAP, DTCs
- **DTCs activos en el auto de prueba:** P0171 (mezcla pobre banco 1), P0420 (catalizador ineficiente)

> **Nota sobre la MAC:** Podemos conectar directo por MAC `50:88:06:D9:14:22` en el firmware
> — mas confiable que buscar por nombre. Si en el futuro se usa otro FD10, se actualiza config.h.
>
> **UUIDs GATT verificados con nRF Connect (2026-03-11):**
> - Service: `FFF0`
> - TX (enviar AT commands): `FFF2` — WRITE
> - RX (leer respuestas): `FFF1` — NOTIFY, READ
> - Device type: CLASSIC and LE (dual-mode, nosotros usamos el BLE/LE)
> - Service secundario `AE00` ignorado (probablemente OTA firmware)

### Herramientas
- PC con PlatformIO (VSCode extension)
- Cable USB-C (para flashear el ESP32)

> **Nota:** El ESP32-S3 SuperMini HW-747 V0.0.2 ya viene con los pines soldados. No necesitamos soldador para el prototipo.

---

## 3. Pinout y cableado

### ESP32-S3 SuperMini HW-747 V0.0.2

Pinout real (verificado de la serigrafía del dorso):

```
    FRENTE (chip visible)         DORSO (label "Super Mini ESP32-S3 HW-747")
            USB-C                           USB-C
        ┌─────────────┐               ┌─────────────┐
   TX  -|             |- 5V      5V  -|             |- TX
   RX  -|             |- GND    GND  -|             |- RX
  B00  -|             |- 3V3    3V3  -|             |-
    1  -|  ESP32-S3   |- 13      13  -|             |- 34
    2  -|  SuperMini  |- 12      33  -|             |- 21
    3  -|  (HW-747)   |- 11      18  -|             |-
    4  -|             |- 10      17  -|  ESP32-S3   |-
    5  -|             |- 48      16  -|  SuperMini  |-
    6  -|             |- 9       15  -|  (dorso)    |-
    7  -|   [C3 LED]  |- 8      14  -|             |-
        └─────────────┘                └─────────────┘

Pines del frente (los que usaremos):
  Izquierda: TX, RX, B00 (boot), GPIO 1-7
  Derecha:   5V, GND, 3V3, GPIO 8-13, 48
```

### MCP2515 HW-184 module pinout

Pines (de izquierda a derecha, serigrafía del PCB):

```
  Pines header (abajo):
    INT — SCK — SI — SO — CS — GND — VCC

  Screw terminal (arriba):
    H (CAN High) — L (CAN Low)
```

Chips: MCP2515 (CAN controller, SPI) + TJA1050 (CAN transceiver)
Cristal: 8 MHz

### Conexion ESP32-S3 SuperMini ↔ MCP2515

| MCP2515 pin | ESP32-S3 pin | Funcion |
|-------------|-------------|---------|
| VCC | 5V | Alimentacion (el HW-184 tiene regulador, acepta 5V) |
| GND | GND | Tierra comun |
| CS | GPIO 7 | SPI Chip Select |
| SI (MOSI) | GPIO 11 | SPI Master Out → Slave In |
| SO (MISO) | GPIO 9 | SPI Slave Out → Master In |
| SCK | GPIO 12 | SPI Clock |
| INT | GPIO 3 | Interrupt (CAN message ready) |

> **NOTA sobre voltaje:** El modulo HW-184 tiene un regulador de 5V a 3.3V onboard para el MCP2515. Alimentar con 5V del ESP32. Las lineas SPI (CS, MOSI, MISO, SCK, INT) operan a 3.3V — compatible directo con el ESP32-S3.
>
> **NOTA sobre SPI:** Los pines SPI son configurables por software en el ESP32-S3. Si hay conflicto, se pueden cambiar en el firmware.

### Conexion MCP2515 ↔ OBD-II pigtail

El pigtail tiene 16 cables (hilos sueltos). Solo necesitamos 3:

| OBD-II Pin | Color (verificar) | Funcion | Conectar a |
|------------|-------------------|---------|------------|
| Pin 6 | — | CAN High | MCP2515 CANH |
| Pin 14 | — | CAN Low | MCP2515 CANL |
| Pin 4 o 5 | — | GND chassis/signal | GND comun |
| Pin 16 | — | +12V bateria | **NO conectar directo al ESP32** (solo si usamos regulador 12V→3.3V) |

> **IMPORTANTE:** Para el prototipo, alimentamos el ESP32 por USB-C desde una powerbank o el celular. NO usamos los 12V del OBD-II hasta tener un regulador de voltaje (tenemos MT3608 pero es step-up, necesitariamos un step-down o LDO para 12V→3.3V).
>
> **Nota Honda CR-V 2010:** Protocolo confirmado CAN 29-bit/500 kbps (extended frame).
> Para Fase 3B con MCP2515: usar `CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ)` y enviar
> requests con extended ID: `CAN.sendMsgBuf(0x7DF, 1, 8, request)` (el `1` = extended frame).

---

## 4. Pasos de implementacion

### Fase 1 — Blink test (validar hardware ESP32-S3) ✅ COMPLETADA (2026-03-11)

**Objetivo:** Confirmar que PlatformIO reconoce el ESP32-S3 SuperMini.

**Resultado:** LED parpadeando, Serial Monitor funcionando. Pipeline de flash establecido.

#### Setup de flash desde WSL2 (resuelto)

El ESP32-S3 SuperMini HW-747 usa USB nativo CDC (VID:PID `303a:1001`). Desde WSL2 no es
accesible directamente — se necesita **usbipd-win** para pasarlo a Linux.

**Setup usbipd-win (una sola vez):**
```powershell
# PowerShell como Administrador
winget install usbipd
# Reiniciar PowerShell, luego:
usbipd bind --busid 1-1   # BUSID del ESP32 (verificar con usbipd list)
```

**Regla udev para permisos (WSL2, una sola vez):**
```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="303a", MODE="0666"' | sudo tee /etc/udev/rules.d/99-esp32.rules
sudo udevadm control --reload-rules
```

**Flujo de flash (cada vez):**
```powershell
# PowerShell:
usbipd attach --wsl --busid 1-1
```
Luego en VSCode: botón **→ Upload** de PlatformIO (o `pio run --target upload` en WSL2).

**`platformio.ini` final (verificado funcionando):**
```ini
[env:esp32s3-supermini]
platform = espressif32
board = lolin_s3_mini
framework = arduino
monitor_speed = 115200
upload_speed = 921600
upload_protocol = esp-builtin   ; JTAG built-in — requerido con usbipd-win
upload_port = /dev/ttyACM0
monitor_port = /dev/ttyACM0
build_flags =
    -DARDUINO_USB_MODE=1
    -DARDUINO_USB_CDC_ON_BOOT=1
```

> **Nota `upload_protocol = esp-builtin`:** El protocolo `esptool` (default) requiere que
> `/dev/ttyACM0` esté estable durante el reset. Con usbipd-win el device se desconecta
> brevemente al hacer reset (~2s), lo que falla el upload. El protocolo `esp-builtin` usa
> OpenOCD via JTAG USB — más robusto con usbipd.

**Firmware Fase 1 (`bridge/firmware/src/main.cpp`):**

```cpp
// ScouterBridge — Fase 1: Blink test
#include <Arduino.h>

#define LED_PIN 21  // GPIO 21 en el SuperMini HW-747

void setup() {
    Serial.begin(115200);
    delay(1000);
    pinMode(LED_PIN, OUTPUT);
    Serial.println("ScouterBridge v0.1 — Fase 1 Blink");
    Serial.printf("LED en GPIO %d\n", LED_PIN);
}

void loop() {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("ON");
    delay(500);
    digitalWrite(LED_PIN, LOW);
    Serial.println("OFF");
    delay(500);
}
```

**Test de exito:** ✅ LED parpadea, Serial Monitor muestra ON/OFF cada 500ms.

### Fase 2 — WiFi + MQTT publish (Bridge con datos dummy) ✅ COMPLETADA (2026-03-11)

**Objetivo:** ESP32 se conecta a WiFi y publica datos dummy en el mismo topic que el emulador.

**Resultado:** HUD recibe datos del ESP32. Pipeline completo `ESP32 → WiFi → MQTT → HUD` funcionando.
Serial Monitor confirmó publicación a 2 Hz:
```
→ rpm=1786 spd=2 cool=84.7 fuel=64.9 bat=14.03
→ rpm=1835 spd=0 cool=84.8 fuel=64.9 bat=14.04
```
HUD log confirmó recepción:
```
Connected to device: car-001
Device metadata: name=Mi Auto - Honda CR-V 2010, type=vehicle.obd2
First data received — display should update now
```

```cpp
// Pseudocodigo Fase 2
#include <WiFi.h>
#include <PubSubClient.h>  // MQTT
#include <ArduinoJson.h>

const char* WIFI_SSID = "TuRedWiFi";
const char* WIFI_PASS = "password";
const char* MQTT_BROKER = "192.168.1.87";
const int   MQTT_PORT = 1883;
const char* DATA_TOPIC = "vehicles/car001/obd2";
const char* META_TOPIC = "vehicles/car001/obd2/$meta";

WiFiClient net;
PubSubClient mqtt(net);

void publishMeta() {
    StaticJsonDocument<512> meta;
    meta["v"] = 1;
    meta["id"] = "car-001";
    meta["name"] = "Mi Auto - Honda CR-V 2010";
    meta["type"] = "vehicle.obd2";
    meta["icon"] = "car";
    meta["refresh_ms"] = 500;
    meta["layout"] = "auto";

    JsonObject schema = meta.createNestedObject("schema");
    // ... (schema fields igual que el emulador)

    char buf[512];
    serializeJson(meta, buf);
    mqtt.publish(META_TOPIC, buf, true);  // retained
}

void publishData() {
    StaticJsonDocument<256> data;
    data["ts"] = (int)(millis() / 1000);
    data["rpm"] = 2000 + random(-200, 200);      // dummy
    data["speed_kmh"] = 40 + random(-10, 10);     // dummy
    data["coolant_temp_c"] = 88.0;                // dummy
    data["fuel_pct"] = 65.0;                      // dummy
    data["battery_v"] = 14.1;                     // dummy
    data["dtc_codes"] = "[]";                     // dummy

    char buf[256];
    serializeJson(data, buf);
    mqtt.publish(DATA_TOPIC, buf);
}

void setup() {
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    // esperar conexion...
    mqtt.setServer(MQTT_BROKER, MQTT_PORT);
    mqtt.connect("scouter-bridge-001");
    publishMeta();
}

void loop() {
    mqtt.loop();
    publishData();
    delay(500);  // 2 Hz como el emulador
}
```

**Test de exito:**
1. Parar el emulador Python en la PC
2. El ESP32 publica datos dummy
3. El HUD (en Pi o preview) muestra los datos del Bridge
4. No se distingue del emulador (mismo formato, mismo topic)

### Fase 3A — Leer OBD-II via FNIRSI FD10 BLE (Demo v1, RECOMENDADO PRIMERO)

**Objetivo:** ESP32 se conecta al FD10 por BLE, lee PIDs reales del auto, publica por MQTT.

**Por que primero:** Zero cableado, zero riesgo, valida end-to-end con datos reales.

**UUIDs confirmados con nRF Connect (2026-03-11) — listo para codear:**

| UUID | Nombre | Properties | Uso |
|------|--------|-----------|-----|
| `FFF0` | OBD Service | PRIMARY SERVICE | Service principal |
| `FFF1` | RX Characteristic | NOTIFY, READ | Leer respuestas del FD10 |
| `FFF2` | TX Characteristic | WRITE | Enviar AT commands al FD10 |

```cpp
// Pseudocodigo Fase 3A — FNIRSI FD10 via BLE (NimBLE)
#include <NimBLEDevice.h>

// UUIDs verificados con nRF Connect (2026-03-11) — FNIRSI FD10, MAC 50:88:06:D9:14:22
#define OBD_SERVICE_UUID        "FFF0"    // Primary Service (confirmado)
#define OBD_TX_CHAR_UUID        "FFF2"    // WRITE — enviamos AT commands aqui
#define OBD_RX_CHAR_UUID        "FFF1"    // NOTIFY + READ — leemos respuestas aqui
// Nota: hay un service secundario AE00 (AE01=WRITE NO RESPONSE, AE02=NOTIFY)
//       probablemente firmware update — no lo usamos

NimBLEClient* pClient = nullptr;
NimBLERemoteCharacteristic* pTxChar = nullptr;
NimBLERemoteCharacteristic* pRxChar = nullptr;

// Buffer para respuesta BLE (se llena via notify callback)
String bleResponse = "";
bool responseReady = false;

// Callback cuando el FD10 envia datos (notify)
void notifyCallback(NimBLERemoteCharacteristic* pChar,
                    uint8_t* pData, size_t length, bool isNotify) {
    for (size_t i = 0; i < length; i++) {
        char c = (char)pData[i];
        if (c == '>') {
            responseReady = true;  // ELM327 prompt = fin de respuesta
            return;
        }
        bleResponse += c;
    }
}

bool connectToFD10() {
    NimBLEDevice::init("ScouterBridge");

    // Conectar directamente por MAC (mas confiable que scan por nombre)
    // MAC verificada del FNIRSI FD10: 50:88:06:D9:14:22
    NimBLEAddress fd10Mac("50:88:06:D9:14:22");
    Serial.println("Conectando al FD10 por MAC...");

    pClient = NimBLEDevice::createClient();
    if (!pClient->connect(fd10Mac)) {
        Serial.println("Fallo conexion BLE — verificar MAC o que el FD10 este enchufado");
        return false;
    }
    Serial.println("Conectado al FD10!");

    // Obtener service y characteristics
    NimBLERemoteService* pService = pClient->getService(OBD_SERVICE_UUID);
    if (!pService) {
        Serial.println("Service no encontrado — verificar UUID con nRF Connect");
        return false;
    }

    pTxChar = pService->getCharacteristic(OBD_TX_CHAR_UUID);
    pRxChar = pService->getCharacteristic(OBD_RX_CHAR_UUID);

    if (!pTxChar || !pRxChar) {
        Serial.println("Characteristics no encontradas — verificar UUIDs");
        return false;
    }

    // Subscribirse a notificaciones (respuestas del FD10)
    pRxChar->subscribe(true, notifyCallback);
    Serial.println("Conectado al FD10!");
    return true;
}

String sendAT(const char* cmd) {
    bleResponse = "";
    responseReady = false;

    // Enviar AT command + CR al FD10
    String cmdStr = String(cmd) + "\r";
    pTxChar->writeValue((uint8_t*)cmdStr.c_str(), cmdStr.length(), false);

    // Esperar respuesta (notify callback la llena)
    unsigned long timeout = millis() + 2000;
    while (!responseReady && millis() < timeout) {
        delay(10);  // yield para que BLE stack procese
    }

    bleResponse.trim();
    return bleResponse;
}

void initOBD() {
    sendAT("ATZ");    // Reset
    delay(1000);
    sendAT("ATE0");   // Disable echo
    sendAT("ATL0");   // Disable linefeeds
    sendAT("ATSP0");  // Auto-detect protocol
}

int readPID(const char* pid_cmd, int byteA_pos) {
    for (int retry = 0; retry < 3; retry++) {
        String resp = sendAT(pid_cmd);

        // Validar formato: "41 XX YY [ZZ]"
        if (resp.startsWith("41")) {
            return parseHexByte(resp, byteA_pos);
        }

        if (resp.indexOf("NO DATA") >= 0 || resp.indexOf("UNABLE") >= 0) {
            delay(100);
            continue;
        }
    }
    return -1;
}

void publishRealData() {
    // Leer PIDs secuencialmente (ELM327 es half-duplex)
    // NOTA: "010C" devuelve "41 0C AA BB" — ambos bytes en una respuesta
    String rpmResp = sendAT("010C");
    int speed = readPID("010D", 2);
    int coolant = readPID("0105", 2);
    int fuel = readPID("012F", 2);

    StaticJsonDocument<256> data;
    data["ts"] = (int)(millis() / 1000);
    // Parsear RPM de la respuesta completa "41 0C AA BB"
    if (rpmResp.startsWith("41")) {
        int A = parseHexByte(rpmResp, 2);
        int B = parseHexByte(rpmResp, 3);
        if (A >= 0 && B >= 0) data["rpm"] = ((A * 256) + B) / 4;
    }
    if (speed >= 0) data["speed_kmh"] = speed;
    if (coolant >= 0) data["coolant_temp_c"] = coolant - 40;
    if (fuel >= 0) data["fuel_pct"] = (fuel * 100) / 255;
    data["battery_v"] = 0;  // usar PID 0x42 si el FD10 lo soporta
    data["dtc_codes"] = "[]";

    char buf[256];
    serializeJson(data, buf);
    mqtt.publish(DATA_TOPIC, buf);
}
```

**AT Commands (mismos para cualquier ELM327-compatible):**

| Comando | Descripcion | Respuesta esperada |
|---------|-------------|-------------------|
| `ATZ` | Reset | `ELM327 vX.X` (version del FD10) |
| `ATE0` | Disable echo | `OK` |
| `ATL0` | Disable linefeeds | `OK` |
| `ATSP0` | Auto-detect protocol | `OK` |
| `010C` | Engine RPM | `41 0C 1A F8` → 1726 RPM |
| `010D` | Vehicle speed | `41 0D 3C` → 60 km/h |
| `0105` | Coolant temp | `41 05 7B` → 83°C |
| `012F` | Fuel level | `41 2F 80` → 50.2% |
| `0142` | Control module voltage | `41 42 37 DC` → 14.3V |

**Error handling:**
- Timeout 2 segundos por comando AT
- 3 reintentos en `NO DATA` o `UNABLE TO CONNECT`
- Validar que la respuesta empiece con `41 XX` antes de parsear
- Validar PIDs contra app **YMOBD** (app oficial del FD10) antes de implementar

**Test de exito:**
1. ESP32 encuentra y conecta al FD10 por BLE automaticamente
2. FD10 enchufado al OBD-II del auto, motor encendido
3. El HUD muestra RPM, velocidad, temperatura REALES
4. Acelerar → RPM sube en el HUD

### Fase 3B — Leer CAN bus directo via MCP2515 (Demo v2, despues)

**Objetivo:** Leer PIDs OBD-II sin intermediario ELM327 — menor latencia, mas control.

Dependencias PlatformIO:
```ini
lib_deps =
    knolleary/PubSubClient@^2.8
    bblanchon/ArduinoJson@^7.0
    coryjfowler/mcp_can@^1.5
```

PIDs OBD-II estandar que necesitamos:

| PID | Nombre | Bytes | Formula | Campo JSON |
|-----|--------|-------|---------|------------|
| 0x0C | RPM | 2 | `((A*256)+B)/4` | `rpm` |
| 0x0D | Speed | 1 | `A` (km/h) | `speed_kmh` |
| 0x05 | Coolant temp | 1 | `A - 40` (C) | `coolant_temp_c` |
| 0x2F | Fuel level | 1 | `(A*100)/255` (%) | `fuel_pct` |
| 0x42 | Control module voltage | 2 | `((A*256)+B)/1000` (V) | `battery_v` |
| 0x01 | DTCs count + MIL | 4 | Bit A7 = MIL on/off | `dtc_codes` |

Flujo CAN bus para leer un PID:

```
ESP32 → CAN bus:  ID=0x7DF, Data=[0x02, 0x01, PID, 0, 0, 0, 0, 0]
                  (request: service 01, PID=X)

Auto → CAN bus:   ID=0x7E8, Data=[0x03, 0x41, PID, A, B, ...]
                  (response: service 41, PID=X, datos)
```

```cpp
// Pseudocodigo Fase 3B — CAN read directo
#include <mcp_can.h>

MCP_CAN CAN(CS_PIN);  // GPIO 7

int readPID(uint8_t pid) {
    uint8_t request[8] = {0x02, 0x01, pid, 0, 0, 0, 0, 0};
    CAN.sendMsgBuf(0x7DF, 0, 8, request);

    unsigned long timeout = millis() + 100;
    while (millis() < timeout) {
        if (CAN.checkReceive() == CAN_MSGAVAIL) {
            uint8_t len;
            uint8_t buf[8];
            unsigned long id;
            CAN.readMsgBuf(&id, &len, buf);

            if (id == 0x7E8 && buf[2] == pid) {
                return buf[3];  // byte A (simplificado)
            }
        }
    }
    return -1;  // timeout
}

void publishRealData() {
    int rpm_raw_A = readPID(0x0C);    // necesita 2 bytes
    int speed = readPID(0x0D);
    int coolant = readPID(0x05);
    // ... etc

    // Mismo JSON que antes, pero con datos reales
    data["rpm"] = rpm;
    data["speed_kmh"] = speed;
    data["coolant_temp_c"] = coolant - 40;
    // ...
}
```

**Test de exito:**
1. ESP32 + MCP2515 conectado al OBD-II del auto (motor encendido)
2. El HUD muestra RPM, velocidad, temperatura REALES
3. Acelerar el auto → RPM sube en el HUD en tiempo real

### Fase 4 — QR code + metadata

**Objetivo:** El Bridge publica `$meta` retained y tiene un QR impreso.

1. Al conectar, el Bridge publica `$meta` en `vehicles/car001/obd2/$meta` (retained)
2. El QR code es estatico: `qrlink://v1/car-001/mqtt/{broker}:1883?t=vehicles/car001/obd2`
3. Lo generamos con el script existente (`emulator/generate_all_qrs.py`) o lo imprimimos manual

**Test de exito:** Escanear el QR con la ScouterApp → el HUD muestra datos reales del auto. Mismo flujo que con el emulador, pero datos reales.

---

## 5. Criterios de exito por fase

| Fase | Test | Como verificar |
|------|------|---------------|
| 1. Blink ✅ | LED parpadea, Serial Monitor muestra texto | Visual + PlatformIO Serial Monitor |
| 2. MQTT ✅ | HUD muestra datos dummy del Bridge (sin emulador) | Parar emulador, iniciar Bridge, ver HUD |
| 3A. ELM327 | HUD muestra RPM/speed reales via ELM327 BT | Motor encendido, acelerar = RPM sube |
| 3B. CAN | HUD muestra RPM/speed reales via MCP2515 directo | Motor encendido, sin ELM327 |
| 4. QR | Escanear QR → conecta al Bridge → datos reales | ScouterApp scan → HUD muestra datos |

---

## 6. Que parte del ecosistema funciona con cada fase

### Despues de Fase 2 (WiFi + MQTT dummy):
```
[ESP32 Bridge] → MQTT → [Broker] → [Pi HUD + ScouterApp]
    datos dummy            ↑
                      mismo topic que el emulador
```
- **Validado:** El Bridge puede reemplazar al emulador
- **El HUD no necesita cambios** — consume el mismo JSON
- **La App no necesita cambios** — misma conexion MQTT via QR
- **Ecosistema funcional:** Bridge + Broker + HUD + App (4/4 componentes reales)

### Despues de Fase 3A (FNIRSI FD10 BLE — datos reales):
```
[Auto OBD-II] → [FNIRSI FD10] → BLE 5.1 → [ESP32 Bridge] → WiFi/MQTT → [Broker] → [Pi HUD]
   datos reales   enchufado      wireless                                                ↕ WS
                                                                                    [ScouterApp]
                                                                                    AI analiza datos
                                                                                    reales del auto
```
- **Validado:** End-to-end con datos reales de un vehiculo
- **AI context real:** El LLM en el phone ve datos reales del motor
- **Demo killer:** "Esto lee datos reales de mi auto y los muestra en un HUD con AI local"
- **Zero cableado:** Solo enchufar el FD10, el ESP32 se conecta por BLE automaticamente

### Despues de Fase 3B (MCP2515 — CAN directo):
- **Upgrade path:** Elimina el ELM327 como intermediario
- **Menor latencia:** ~50ms vs ~300-500ms
- **Mas control:** Acceso a todos los PIDs, no solo los que el ELM327 soporta
- **Producto standalone:** Un solo dispositivo (ESP32 + MCP2515) reemplaza al scanner comercial

### Despues de Fase 4 (QR code):
- **El Bridge es un producto completo:** Enchufar al auto → escanear QR → ver datos
- **No necesita PC** — Solo el Bridge + broker (puede correr en Pi o cualquier servidor)
- **Setup en 2 minutos:** Enchufar, conectar WiFi, escanear QR, listo

---

## 7. Riesgos y mitigaciones

| Riesgo | Probabilidad | Aplica a | Mitigacion |
|--------|-------------|----------|------------|
| SuperMini no reconocido por PlatformIO | Media | Todas | Probar board definitions: `lolin_s3_mini`, `esp32-s3-devkitc-1`, `esp32s3box` |
| FD10 no encontrado por BLE scan | Media | 3A | Verificar nombre BLE con nRF Connect. Probar scan por service UUID si el nombre no aparece |
| UUIDs del FD10 no son estandar | Media | 3A | Usar nRF Connect para descubrir services/characteristics reales. Algunos usan FFF0, otros FFE0, otros custom |
| BLE UART lento (~300-500ms por PID) | Alta | 3A | Aceptable para HUD no-safety. Leer solo 4-5 PIDs por ciclo. Rotar PIDs si son muchos |
| MCP2515 modulo opera a 5V, ESP32 a 3.3V | Alta | 3B | El modulo HW-184 tiene regulador propio. Alimentar con 5V del USB, lineas SPI son 3.3V tolerant |
| El auto no responde a PID requests | Baja | 3A/3B | Honda CR-V 2010 usa ISO 15765-4 CAN 29-bit/500 kbps (confirmado con YMOBD). Probar primero con PID 0x00 |
| CAN bus frame type incorrecto | Baja | 3B | Honda CR-V 2010 usa CAN 29-bit (extended IDs). Configurar MCP2515 para extended frame. Si no responde, probar 11-bit |
| WiFi del auto/celular inestable | Media | Todas | Para el prototipo, usar hotspot del celular. Despues, WiFi hardcodeado |

---

## 8. Estructura de archivos

```
scouterhud/
└── bridge/
    └── firmware/
        ├── platformio.ini
        ├── src/
        │   ├── main.cpp           ← Entry point
        │   ├── config.h           ← WiFi, MQTT, BLE UUIDs, PIDs
        │   ├── obd_ble.h          ← NimBLE client para FNIRSI FD10
        │   ├── obd_ble.cpp
        │   ├── can_reader.h       ← MCP2515 wrapper (Fase 3B)
        │   ├── can_reader.cpp
        │   ├── mqtt_bridge.h      ← MQTT client + QR-Link format
        │   ├── mqtt_bridge.cpp
        │   └── led_status.h       ← LED patterns (opcional)
        └── README.md
```

Empezamos simple — sin plugin system, sin portal captive, sin OTA. Solo: leer OBD → publicar MQTT. Lo demas viene despues.

---

## 9. Dependencias PlatformIO

### Demo v1 (FNIRSI FD10 BLE) — Fases 1, 2, 3A:
```ini
[env:esp32s3-supermini]
platform = espressif32
board = lolin_s3_mini
framework = arduino
monitor_speed = 115200
upload_speed = 921600

lib_deps =
    knolleary/PubSubClient@^2.8
    bblanchon/ArduinoJson@^7.0
    h2zero/NimBLE-Arduino@^1.4

build_flags =
    -DARDUINO_USB_MODE=1
    -DARDUINO_USB_CDC_ON_BOOT=1
```

> **Nota:** Usamos `NimBLE-Arduino` (mas liviano que la stack BLE default del ESP32).
> NimBLE soporta BLE client mode que necesitamos para conectar al FD10.

### Demo v2 (MCP2515 directo) — Fase 3B:
```ini
lib_deps =
    knolleary/PubSubClient@^2.8
    bblanchon/ArduinoJson@^7.0
    coryjfowler/mcp_can@^1.5
```

---

## 10. Proxima sesion (plan recomendado)

**Todo listo para empezar — checklist:**

- [x] UUIDs del FD10 confirmados con nRF Connect
- [x] MAC del FD10 anotada: `50:88:06:D9:14:22`
- [x] PIDs confirmados funcionando con YMOBD
- [x] Protocolo del auto confirmado: CAN 29-bit/500 kbps

**Pasos siguientes:**

1. ~~Instalar PlatformIO en VSCode~~ ✅
2. ~~Fase 1: Blink test con ESP32-S3 SuperMini~~ ✅ (2026-03-11)
3. ~~Fase 2: WiFi + MQTT publish (reemplazar emulador con datos dummy)~~ ✅ (2026-03-11)
4. Fase 3A: Conectar al FD10 por BLE + leer PIDs reales del auto

---

## 11. Relacion con documento anterior

El doc `scouterbridge-demo-v1(1).md` planteaba usar BLE GATT para Bridge→HUD. Ese approach
fue reemplazado por **WiFi/MQTT** que es lo que el ecosistema usa actualmente. Las diferencias:

| Aspecto | Doc anterior (v1) | Este doc (actual) |
|---------|-------------------|-------------------|
| Bridge → HUD | BLE GATT | WiFi / MQTT via Broker |
| Protocolo | Custom BLE service | QR-Link (mismo que emulador) |
| Requiere cambios al HUD | Si (nuevo BLE receiver) | No (misma conexion MQTT) |
| Multi-device | Dificil (BLE 1:1) | Natural (multiples topics MQTT) |

El approach MQTT es superior porque **el HUD no necesita ningun cambio** — ya consume
datos MQTT del emulador, y el Bridge publica en el mismo topic con el mismo JSON.
