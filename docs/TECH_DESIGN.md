# ScouterHUD — Open Source AI-Powered Monocular HUD

## Technical Design Document v0.2

**Project Codename:** ScouterHUD  
**Author:** Ger  
**Date:** February 2026  
**License:** MIT (Software) / CERN-OHL-S v2 (Hardware)  
**Status:** Pre-prototype / Planning  
**Revision:** v0.2 — Added QR-Link protocol, see-through optics, camera module

---

## 1. Vision & Scope

### 1.1 Qué es ScouterHUD

Un heads-up display monocular wearable de bajo costo, open source, basado en Raspberry Pi, con integración de IA y descubrimiento contextual de dispositivos via QR. Inspirado en el scouter de Dragon Ball Z: una vincha que sostiene una pantalla semitransparente frente a un ojo, con procesamiento, audio y batería distribuidos alrededor de la cabeza.

**Innovación clave: QR-Link Protocol.** El usuario mira un código QR pegado en cualquier dispositivo (auto, monitor médico, sensor IoT, servidor) y el ScouterHUD se conecta automáticamente para mostrar datos en vivo superpuestos en su campo visual. No es AR convencional — es mejor: es un sistema de descubrimiento contextual visual que funciona con hardware de $60.

### 1.2 Qué NO es

- No es AR con tracking espacial (no hay SLAM ni depth sensing)
- No es un reemplazo de Google Glass, HoloLens o Apple Vision Pro
- No compite con dispositivos de $300+ como Brilliant Monocle en pulido de producto
- No requiere que los dispositivos target tengan hardware especial — solo un QR impreso

### 1.3 Propuesta de valor

- **100% open source** (hardware + software + protocolo + docs)
- **Costo total < $65 USD** para el MVP
- **AI-first**: diseñado para ser una interfaz wearable hacia LLMs y agentes de IA
- **QR-Link**: protocolo abierto de descubrimiento visual de dispositivos
- **See-through**: display semitransparente que no bloquea la visión
- **Modular**: cada componente es reemplazable e imprimible en 3D
- **Documentación de calidad**: BOM claro, guías de armado, fotos de cada paso

### 1.4 Casos de uso

**QR-Link (feature estrella):**
- Mirar el QR de un monitor de respiración médica → ver SpO2, frecuencia, alertas en pantalla
- Mirar el QR del auto → ver datos OBD-II (RPM, temperatura, códigos de error)
- Mirar el QR de un rack de servidores → ver métricas de CloudWatch, costos, alertas
- Mirar el QR de una máquina industrial → ver estado, temperatura, ciclos
- Mirar el QR de un electrodoméstico → ver temperatura, estado, consumo

**Asistente IA:**
- Asistente de voz manos libres (STT → LLM → TTS + display)
- Traducción en tiempo real (audio → texto en pantalla)
- Teleprompter / notas flotantes

**Utilidades:**
- Notificaciones del celular via Bluetooth
- Reloj, clima, métricas personales

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama de bloques

```
┌───────────────────────────────────────────────────────────────┐
│                      HEADBAND FRAME                           │
│                    (3D printed, PETG)                          │
│                                                               │
│  ┌────────────┐    ┌───────────┐    ┌──────────────────────┐  │
│  │ DISPLAY    │◄───│  RPi Zero │───►│  AUDIO OUTPUT        │  │
│  │ + beam     │SPI │  2W       │    │  (earpiece)          │  │
│  │ splitter   │    │           │    └──────────────────────┘  │
│  └────────────┘    │  ┌─────┐  │     (oído derecho)          │
│   (ojo derecho)    │  │WiFi │  │                              │
│                    │  │ BT  │  │    ┌──────────────────────┐  │
│  ┌────────────┐    │  └─────┘  │    │  MICROPHONE          │  │
│  │ PI CAMERA  │───►│           │    │  (MEMS / USB)        │  │
│  │ (QR scan)  │CSI │  GPIO     │    └──────────────────────┘  │
│  └────────────┘    └─────┬─────┘     (cerca de boca)         │
│   (junto al display)     │                                    │
│                    ┌─────▼─────┐                              │
│                    │ BATTERY   │                              │
│                    │ + BMS     │                              │
│                    └───────────┘                              │
│                     (nuca/contrapeso)                         │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 Distribución física en la vincha

```
          FRENTE (frente de la cabeza)
                ┌───────────┐
               / beam splitter\
              /   + cámara     \
      ┌──────┐    + display     ┌──────┐
      │ pad  │                  │ RPi  │
      │ foam │                  │ Zero │
      │(left)│                  │ +mic │
      │      │                  │+audio│
      └──┬───┘                  └──┬───┘
         │      NUCA (atrás)      │
         │    ┌──────────────┐    │
         └────│   BATTERY    │────┘
              │   + BMS      │
              │   + USB-C    │
              └──────────────┘
           (contrapeso natural)
```

### 2.3 Sistema óptico See-Through

```
                    Vista lateral (corte)

                         ┌─── Beam Splitter (acrílico 45°)
                         │       semitransparente
                         │      /
    [MUNDO REAL] ─ luz ─┼────/────────────► [OJO]
                         │  / ▲
                         │/   │ reflejo
                         /    │
                        /     │
                    [DISPLAY TFT]     [PI CAMERA]
                    (cara arriba)     (mira al frente)
                    ilumina hacia     captura QR codes
                    el splitter       del mundo real

    Resultado: El ojo ve simultáneamente:
    - El mundo real (luz que atraviesa el splitter)
    - Los datos del display (luz reflejada por el splitter)
```

**Principio óptico:** El beam splitter es simplemente un pedazo de acrílico transparente (o vidrio) posicionado a 45° entre el ojo y el mundo. El display se coloca perpendicular (cara arriba o lateral), su luz rebota en el acrílico hacia el ojo. La luz del mundo real pasa a través del acrílico con ~50-70% de transmisión.

**Opciones de beam splitter para MVP:**

| Opción | Costo | Calidad | Notas |
|--------|-------|---------|-------|
| Acrílico transparente cortado (caja de CD) | $0 | Baja | Prueba de concepto rápida |
| Acrílico 1mm con coating anti-reflejo | $2-3 | Media | Buen balance para MVP |
| Vidrio óptico 50/50 beam splitter | $8-15 | Alta | Edmund Optics, mejor imagen |
| Film holográfico semi-espejado | $5-10 | Media-Alta | Flexible, fácil de montar |

**Lente de enfoque:** Se necesita una lente convergente entre el display y el beam splitter para que la imagen se enfoque a distancia cómoda. Lupa asférica de 3-5X (~30mm Ø).

```
    [DISPLAY] ──► [LENTE ASFÉRICA] ──► [BEAM SPLITTER 45°] ──► [OJO]
                   colima la luz         refleja imagen         ve ambos:
                   del display           + deja pasar luz       datos + mundo
                                         del mundo real
```

---

## 3. QR-Link Protocol — Especificación

### 3.1 Concepto

QR-Link es un protocolo abierto que permite a cualquier dispositivo (IoT, vehículo, equipo médico, servidor, electrodoméstico) anunciar su identidad y endpoint de datos a través de un simple código QR impreso. Cuando el ScouterHUD escanea el QR, se conecta al dispositivo y muestra datos en vivo.

```
┌──────────┐   óptico    ┌──────────┐   WiFi/BLE   ┌──────────────┐
│ScouterHUD│──(cámara)──►│ QR Code  │──(contiene)─►│  Dispositivo  │
│          │             │          │              │  (auto,       │
│ muestra  │◄────────────│ ID +     │◄─────────────│  monitor,     │
│ datos    │  datos via  │ protocol │  transmite   │  sensor,      │
│ en vivo  │  WiFi/BLE   │ endpoint │  datos live  │  servidor)    │
└──────────┘              └──────────┘              └──────────────┘
```

### 3.2 Formato del QR Code

#### Diseño compacto (URL-based)

Un QR code estándar (versión 1, error correction M) solo cabe ~134 bytes alfanuméricos. Meter un JSON completo con todos los campos opcionales excedería ese límite fácilmente. Por eso, el QR contiene únicamente la información mínima para **descubrir y conectar** al dispositivo, usando un formato URL compacto:

```
qrlink://v1/{id}/{proto}/{endpoint}[?auth={auth}&t={topic}]
```

**Ejemplos:**

```
qrlink://v1/monitor-bed-12/mqtt/192.168.1.50:1883?auth=pin&t=ward3/bed12/vitals
qrlink://v1/car-001/mqtt/192.168.1.100:1883?t=vehicles/car001/obd2
qrlink://v1/srv-prod-01/http/192.168.1.200:8080?auth=token
```

Esto cabe en ~80-120 bytes, dentro del límite de un QR compacto y escaneable a distancia.

**Campos en la URL (obligatorios):**

| Segmento | Descripción |
|----------|-------------|
| `v1` | Versión del protocolo |
| `{id}` | Identificador único del dispositivo |
| `{proto}` | Protocolo de comunicación: `mqtt`, `http`, `ws`, `ble`, `mdns` |
| `{endpoint}` | Dirección de conexión (host:port) |

**Query params opcionales en la URL:**

| Param | Default | Descripción |
|-------|---------|-------------|
| `auth` | `open` | Método de auth: `open`, `pin`, `token`, `mtls`, `mfa` |
| `t` | null | Topic MQTT o path del recurso |

#### Metadata por endpoint (lookup automático)

Toda la metadata adicional (nombre legible, tipo, ícono, refresh rate, schema, layout) **no va en el QR**. En su lugar, el ScouterHUD la obtiene del propio dispositivo después de conectarse, a través de un **metadata endpoint** estandarizado:

- **MQTT:** El dispositivo publica metadata en `{topic}/$meta` (retained message)
- **HTTP:** GET `{endpoint}/$meta`
- **WebSocket:** Primer mensaje después de connect es el metadata frame

**Formato de metadata (JSON completo, sin restricción de tamaño):**

```json
{
  "v": 1,
  "id": "monitor-bed-12",
  "name": "Monitor Respiratorio Cama 12",
  "type": "medical.respiratory_monitor",
  "icon": "lungs",
  "refresh_ms": 1000,
  "layout": "auto",
  "auth_hint": "Solicite el PIN al personal de enfermería",
  "schema": {
    "spo2": {"unit": "%", "range": [0, 100], "alert_below": 90},
    "heart_rate": {"unit": "bpm", "range": [30, 220], "alert_above": 120},
    "resp_rate": {"unit": "rpm", "range": [5, 40]},
    "temp_c": {"unit": "°C", "range": [35, 42]}
  }
}
```

**Flujo completo:**

```
1. ScouterHUD escanea QR → parsea URL compacta (id, proto, endpoint, auth)
2. Se conecta al endpoint según proto
3. Solicita metadata ($meta topic/endpoint)
4. Recibe JSON completo con name, type, icon, schema, layout, etc.
5. Con el type, selecciona el layout apropiado
6. Se subscribe al stream de datos y renderiza
```

**Ventajas de este diseño:**
- QR pequeño y escaneable a distancia (~80-120 bytes)
- Metadata actualizable sin reimprimir el QR
- Schema extensible sin límites de tamaño
- El QR solo contiene lo mínimo: dónde conectarse y cómo autenticarse

### 3.3 Protocolos de transporte soportados

| Proto value | Protocolo | Caso de uso | Implementación |
|-------------|-----------|-------------|----------------|
| `mqtt` | MQTT 3.1.1/5.0 | IoT, sensores, monitores | `paho-mqtt` |
| `http` | HTTP GET/SSE | APIs REST, dashboards | `aiohttp` |
| `ws` | WebSocket | Datos real-time bidireccionales | `websockets` |
| `ble` | BLE GATT | Dispositivos cercanos sin WiFi | `bleak` |
| `mdns` | mDNS + HTTP | Auto-discovery en LAN | `zeroconf` |

### 3.4 Formato de datos del dispositivo

Los dispositivos transmiten datos como JSON plano. El ScouterHUD renderiza automáticamente basado en el `type` del dispositivo:

**Ejemplo: Monitor respiratorio**
```json
{
  "ts": 1708099200,
  "spo2": 97,
  "resp_rate": 16,
  "heart_rate": 72,
  "temp_c": 36.8,
  "alerts": [],
  "status": "stable"
}
```

**Ejemplo: Auto (OBD-II)**
```json
{
  "ts": 1708099200,
  "rpm": 2400,
  "speed_kmh": 60,
  "coolant_temp_c": 90,
  "fuel_pct": 45,
  "dtc_codes": [],
  "battery_v": 14.2
}
```

**Ejemplo: Servidor / Infraestructura**
```json
{
  "ts": 1708099200,
  "cpu_pct": 34.2,
  "mem_pct": 67.8,
  "disk_pct": 45.0,
  "monthly_cost_usd": 1234.56,
  "active_alerts": 0,
  "instance_id": "i-0abc123def456"
}
```

### 3.5 Device Types y Layouts automáticos

El campo `type` usa un namespace jerárquico que determina cómo se renderizan los datos:

```
medical.*                → Colores verde/amarillo/rojo, alertas prominentes
  medical.respiratory_monitor
  medical.pulse_oximeter
  medical.infusion_pump
  medical.vital_signs

vehicle.*                → Gauges circulares, iconos de auto
  vehicle.obd2
  vehicle.tire_pressure
  vehicle.ev_battery

infra.*                  → Métricas tipo dashboard, costos
  infra.server
  infra.aws_instance
  infra.kubernetes_pod
  infra.network_switch

home.*                   → Iconos hogareños, temperaturas
  home.thermostat
  home.water_heater
  home.refrigerator
  home.energy_meter

industrial.*             → Métricas técnicas, alertas safety
  industrial.machine
  industrial.temperature_sensor
  industrial.pressure_gauge

custom.*                 → Layout genérico key-value
```

### 3.6 Flujo de conexión completo

```
1. SCAN
   Cámara captura frame → pyzbar detecta QR → parsea JSON
   Tiempo estimado: 100-500ms

2. VALIDATE
   Verifica versión del protocolo
   Verifica que el proto esté soportado
   Chequea si el dispositivo ya fue conectado antes (cache)

3. CONNECT
   Establece conexión al endpoint según proto:
   - MQTT: subscribe al topic
   - HTTP: GET inicial + polling o SSE stream
   - WS: connect + listen
   - BLE: scan + connect + subscribe characteristic

4. RENDER
   Busca layout para el device type
   Si no hay layout específico → usa layout genérico key-value
   Renderiza datos en el beam splitter display
   Actualiza según refresh_ms

5. MAINTAIN
   Reconexión automática si se pierde conexión
   Timeout configurable (default 30s sin datos → desconecta)
   Cache del último estado conocido

6. DISCONNECT
   Trigger: escaneo de nuevo QR, comando de voz "cerrar",
   o timeout sin datos
   Limpia conexión y vuelve a pantalla home
```

### 3.7 Seguridad y autenticación

#### Problema fundamental

El QR es visible para cualquiera que pase cerca del dispositivo. Si el QR contiene acceso directo, cualquier persona con un ScouterHUD (o incluso un celular) podría leer datos privados. La solución es separar **descubrimiento** (el QR te dice que el dispositivo existe y dónde está) de **autorización** (probar que tenés derecho a ver sus datos).

#### Niveles de seguridad (implementación progresiva)

**Nivel 0 — Open (datos públicos)**
- Sin autenticación. El QR da acceso directo.
- Uso: datos no sensibles (temperatura ambiente, estado de máquina pública, señalética interactiva).
- `"auth": "open"` en el QR.

**Nivel 1 — Device PIN (MVP)**
- El QR contiene el endpoint pero NO da acceso.
- Al conectarse, el dispositivo responde con un challenge `AUTH_REQUIRED`.
- El usuario ingresa un PIN de 4-6 dígitos (por voz: "pin uno dos tres cuatro", o pre-configurado en el ScouterHUD).
- El dispositivo valida el PIN y abre el stream de datos.
- El PIN se cachea localmente para reconexiones futuras (con TTL configurable).
- `"auth": "pin"` en el QR.

```
ScouterHUD                          Dispositivo
    │                                    │
    │──── CONNECT (device_id) ──────────►│
    │                                    │
    │◄─── AUTH_REQUIRED (pin) ──────────│
    │                                    │
    │──── AUTH (pin: "1234") ───────────►│
    │                                    │
    │◄─── AUTH_OK + DATA stream ────────│
    │◄─── {spo2: 97, hr: 72, ...} ─────│
    │◄─── {spo2: 96, hr: 74, ...} ─────│
```

**Nivel 2 — Role-based tokens (post-MVP)**
- Un administrador (ej: jefe de enfermería, fleet manager) genera tokens con roles asignados usando una herramienta CLI o web.
- Cada token define: identidad, rol, dispositivos autorizados, expiración.
- Los tokens se pre-cargan en el ScouterHUD del usuario.
- Al escanear un QR, el ScouterHUD envía su token automáticamente.
- El dispositivo valida el token y filtra los datos según el rol.

```json
// Token almacenado en el ScouterHUD
{
  "token_id": "tok_abc123",
  "user": "Dr. García",
  "role": "physician",
  "authorized_types": ["medical.*"],
  "authorized_devices": ["*"],  // todos los médicos
  "issued_by": "Hospital Central Admin",
  "expires": "2026-06-01T00:00:00Z",
  "signature": "hmac_sha256_..."
}
```

- `"auth": "token"` en el QR.
- **Filtrado por rol:** El mismo monitor médico muestra datos diferentes según quién mira:

| Rol | Datos visibles |
|-----|---------------|
| `physician` | Todos los vitales, historial, medicación, alertas |
| `nurse` | Vitales actuales, alertas, última medicación |
| `technician` | Estado del equipo, calibración, batería |
| `family` | Estado general (estable/inestable), alerta si crítico |

**Nivel 3 — Mutual TLS / Certificados (futuro)**
- Cada ScouterHUD tiene un certificado de cliente emitido por una CA interna.
- El dispositivo tiene su propio certificado de servidor.
- Handshake TLS mutuo: ambos lados se autentican.
- Ideal para entornos regulados (hospitales, industria, gobierno).
- Requiere infraestructura PKI (CA server, enrollment, revocación).
- `"auth": "mtls"` en el QR.

**Nivel 4 — Multi-factor: QR + Biométrico (futuro lejano)**
- QR como primer factor (descubrimiento + endpoint).
- Segundo factor: voz del usuario verificada por voiceprint.
- El ScouterHUD captura la voz del usuario diciendo una frase, genera un hash biométrico, y lo envía junto con el token.
- Extremadamente robusto pero requiere enrollment previo.
- `"auth": "mfa"` en el QR.

#### Campo auth en la URL QR

Con el formato URL compacto, el auth se indica como query param:

```
qrlink://v1/monitor-cama-12/mqtt/192.168.1.50:1883?auth=pin&t=ward3/bed12/vitals
```

Los campos adicionales de auth (`auth_hint`, `auth_endpoint`, `roles_available`) se transmiten a través del **metadata endpoint** (`$meta`), no en el QR:

```json
{
  "v": 1,
  "id": "monitor-cama-12",
  "name": "Monitor Respiratorio Cama 12",
  "type": "medical.respiratory_monitor",
  "auth_hint": "Solicite el PIN al personal de enfermería",
  "auth_endpoint": null,
  "roles_available": ["physician", "nurse", "technician", "family"],
  "icon": "lungs",
  "refresh_ms": 1000
}
```

#### Seguridad adicional: Medidas complementarias

**Cifrado de transporte:** Siempre usar TLS/SSL cuando sea posible (MQTTS en vez de MQTT, HTTPS en vez de HTTP, WSS en vez de WS). En el QR, indicar con un flag `"tls": true`.

**Expiración de sesión:** Toda conexión autenticada tiene un TTL. Default: 30 minutos. El ScouterHUD debe re-autenticar después del TTL. Configurable por dispositivo.

**Audit log:** El dispositivo registra quién se conectó, cuándo, y qué datos accedió. Crítico para entornos médicos y compliance (HIPAA, GDPR).

**Rate limiting:** Máximo de intentos de PIN fallidos (3-5) antes de lockout temporal. Protege contra fuerza bruta si alguien copia el QR.

**Disclaimer para datos médicos:** Los dispositivos médicos emulados en este proyecto generan datos **completamente ficticios** con fines de demostración. El protocolo QR-Link en sus niveles 0 y 1 (open/PIN) **NO es apto para uso clínico real**. Cualquier implementación con datos médicos reales DEBE usar nivel 2+ (role-based tokens con TLS) como mínimo, y cumplir con las regulaciones aplicables (HIPAA, GDPR, normativas locales de dispositivos médicos).

**QR rotation (futuro):** Pantallas e-ink en el dispositivo que rotan el QR periódicamente con tokens de corta vida. El QR estático apunta a un endpoint de descubrimiento que genera tokens efímeros.

#### Roadmap de seguridad

| Phase | Nivel | Descripción | Esfuerzo |
|-------|-------|-------------|----------|
| MVP (Phase 1) | 0 + 1 | Open + PIN | 1-2 días |
| Phase 3 | 2 | Role-based tokens + TLS | 1-2 semanas |
| Phase 5+ | 3 | Mutual TLS + PKI | 2-4 semanas |
| Futuro | 4 | MFA biométrico | Investigación |

---

## 4. Bill of Materials (BOM)

### 4.1 Componentes principales

| # | Componente | Modelo recomendado | Precio aprox. | Notas |
|---|-----------|-------------------|---------------|-------|
| 1 | SBC | Raspberry Pi Zero 2W | $15 | Quad-core ARM Cortex-A53, WiFi, BT 4.2 |
| 2 | Display | 1.3" IPS TFT SPI (ST7789) 240x240 | $4-6 | Color, buena visibilidad, SPI rápido |
| 3 | Display ALT | 0.96" OLED SSD1306 128x64 I2C | $3-4 | Monocromático, más simple, menor consumo |
| 4 | Beam Splitter | Acrílico transparente 1mm, ~30x25mm | $1-3 | Cortado a 45°. Alt: caja de CD |
| 5 | Lente | Lupa asférica 3-5X ~30mm diámetro | $2-3 | Colima luz del display hacia el splitter |
| 6 | Cámara | Pi Camera Module OV5647 (compatible) | $4-5 | 5MP, conector CSI, para escaneo QR |
| 7 | Batería | 18650 Li-ion 3000mAh (ej: Samsung 30Q) | $5-8 | ~5-8 hrs autonomía estimada |
| 8 | BMS + Boost | TP4056 + MT3608 módulo | $3-5 | Carga USB-C, boost a 5V estable |
| 9 | BMS ALT | Waveshare Li-ion Battery HAT | $10 | Plug & play, incluye protección |
| 10 | Audio | Auricular intracanal con cable corto | $2-3 | Via USB sound card |
| 11 | Micrófono | USB sound card mini + mic electret | $3-4 | Audio in + out en un módulo |
| 12 | MicroSD | 16-32GB Clase 10 | $5-8 | Para el OS + software |
| 13 | Cables | FFC cable para cámara, jumpers, termocontr. | $3-4 | FFC de 15cm para Pi Camera |
| 14 | Frame | Filamento PETG para impresión 3D | $2-3 | ~60g de material por unidad |
| 15 | Varios | Tornillos M2/M2.5, espuma EVA, velcro | $2-3 | Montaje y confort |

**Costo total estimado MVP:** $50-68 USD

### 4.2 Herramientas necesarias

- Impresora 3D (o servicio de impresión)
- Soldador + estaño (para headers del Pi Zero)
- Multímetro (verificar voltajes)
- Cortador / cutter (para acrílico del beam splitter)
- Destornillador Phillips pequeño
- Pistola de silicona caliente (fijación de componentes)

---

## 5. Hardware — Diseño detallado

### 5.1 Display + Óptica See-Through

**Display recomendado:** TFT SPI 1.3" ST7789 (240x240, color, alto brillo)

El brillo alto es crítico para see-through: la imagen reflejada compite con la luz ambiental. Los TFT IPS tienen mejor brillo que los OLED para este uso.

**Conexión SPI al RPi Zero 2W:**

| Display Pin | RPi GPIO (BCM) | RPi Pin físico | Función |
|------------|---------------|----------------|---------|
| VCC | 3.3V | Pin 1 | Alimentación |
| GND | GND | Pin 6 | Tierra |
| SCL/CLK | GPIO 11 (SCLK) | Pin 23 | SPI Clock |
| SDA/DIN | GPIO 10 (MOSI) | Pin 19 | SPI Data |
| RES/RST | GPIO 25 | Pin 22 | Reset |
| DC | GPIO 24 | Pin 18 | Data/Command |
| CS | GPIO 8 (CE0) | Pin 24 | Chip Select |
| BLK | GPIO 12 | Pin 32 | Backlight PWM |

**Módulo óptico ensamblado:**

```
    Vista lateral del módulo óptico (dentro del housing)

    ┌──────────────── housing impreso 3D ────────────────┐
    │                                                     │
    │  [DISPLAY TFT]                                     │
    │  (cara arriba)                                      │
    │       │                                             │
    │       │ luz                                         │
    │       ▼                                             │
    │  [LENTE ASFÉRICA]                                  │
    │       │                                             │
    │       │ luz colimada                                │
    │       ▼                                             │
    │  [BEAM SPLITTER]────────────────────►  [al OJO]    │
    │  (acrílico 45°) ▲                    (ve datos     │
    │                  │                    + mundo)      │
    │                  │ luz del                          │
    │                  │ mundo real                       │
    │           [APERTURA FRONTAL]                        │
    │                                                     │
    │  [PI CAMERA]  (montada mirando al frente,          │
    │               junto a la apertura)                  │
    │                                                     │
    └─────────────────────────────────────────────────────┘
```

**Beam Splitter DIY:**
1. Cortar un rectángulo de acrílico transparente de ~30x25mm
2. Montar a 45° dentro del housing con ranuras impresas
3. El display ilumina desde abajo/lateral
4. La lente entre display y splitter colima la imagen
5. El ojo recibe: reflejo de datos + luz del mundo real

### 5.2 Cámara (QR Scanner)

**Módulo:** Pi Camera OV5647 (v1.3 compatible) o módulo CSI genérico.

**Conexión:** Cable FFC (flat flex cable) de 15cm al conector CSI del Pi Zero 2W. El Pi Zero usa conector CSI mini, puede necesitar adaptador FFC de 22pin a 15pin.

**Montaje:** La cámara se monta en el housing del display, mirando al frente, cerca de la apertura del beam splitter. Así "ve" lo mismo que el ojo del usuario.

**Configuración de software para QR scanning:**

Resolución de captura para QR: 640x480 es suficiente (menor = más rápido).
La cámara NO necesita estar capturando constantemente. Modo de operación:
1. **Idle:** Sin captura (ahorro de energía)
2. **Scan mode:** Activado por comando de voz ("escanear") o botón
3. **Burst scan:** Captura frames a 5-10 FPS hasta detectar QR
4. **QR found:** Para captura, procesa, conecta al dispositivo

### 5.3 Alimentación

**Esquema de poder:**

```
[18650 3.7V] → [TP4056 charger] → [MT3608 boost 5V] → [RPi 5V pin]
                    ↑                                       │
              [USB-C input]                            [3.3V rail]
               (carga)                                      │
                                                  [Display + Mic + Camera]
```

**Consumo estimado:**

| Componente | Consumo típico | Consumo pico |
|-----------|---------------|-------------|
| RPi Zero 2W (idle + WiFi) | 120 mA | 350 mA |
| Display TFT SPI | 20 mA | 30 mA |
| Pi Camera (durante scan) | 50 mA | 100 mA |
| Micrófono (USB) | 5 mA | 10 mA |
| Audio (auricular) | 5 mA | 15 mA |
| BMS overhead | 10 mA | 20 mA |
| **TOTAL (sin cámara)** | **~160 mA** | **~425 mA** |
| **TOTAL (con cámara activa)** | **~210 mA** | **~525 mA** |

**Autonomía con 18650 3000mAh:**
- Uso normal (cámara intermitente): **~8-12 horas**
- Uso intensivo (WiFi + AI + cámara): **~5-7 horas**
- Estimación conservadora real: **5-8 horas**

### 5.4 Audio — Entrada y salida

**Recomendación MVP (simple y funcional):**
- USB sound card mini (~$2-3) que provee mic input + audio output
- Micrófono electret conectado al input de la sound card
- Auricular intracanal al output 3.5mm de la sound card
- Un solo cable USB desde la sound card al Pi Zero (OTG)
- Evita toda la complejidad I2S

**Upgrade path (post-MVP):**
- INMP441 MEMS mic via I2S para mejor calidad de voz
- MAX98357A DAC + transductor de conducción ósea
- Permite audio sin tapar el oído

### 5.5 Frame / Estructura mecánica

**Piezas del frame (archivos STL):**

```
hardware/3d-models/
├── headband_left.stl         → Brazo izquierdo con padding mount
├── headband_right.stl        → Brazo derecho con rpi mount
├── headband_rear.stl         → Pieza trasera con battery case
├── headband_adjuster.stl     → Mecanismo de ajuste de tamaño (×2)
├── optics_housing.stl        → Housing principal: display + lente + splitter
├── optics_splitter_mount.stl → Soporte del beam splitter a 45°
├── optics_lens_ring.stl      → Anillo ajustable para la lente
├── camera_mount.stl          → Soporte de Pi Camera en el housing
├── rpi_enclosure.stl         → Enclosure del Pi Zero (sobre oreja)
├── battery_case.stl          → Caja 18650 + BMS (nuca)
├── mic_boom.stl              → Mini boom para micrófono
├── cable_clips.stl           → Clips guía de cables (×4)
├── padding_template.dxf      → Template para cortar espuma EVA
└── src/                      → Archivos fuente FreeCAD/OpenSCAD
```

**Especificaciones de impresión:**
- Material: PETG (resistencia + flexibilidad + tolera calor del Pi)
- Relleno: 20-30%
- Capa: 0.2mm
- Sin soportes donde sea posible
- Color recomendado: negro mate (reduce reflejos internos en óptica)
- Peso total estimado del frame: 50-70g

**Peso total del dispositivo ensamblado:**
- Frame: ~60g
- Pi Zero 2W: 10g
- Display + óptica: 15g
- Cámara: 3g
- 18650 + BMS: 50g
- Audio + mic + cables: 15g
- **Total: ~153g** (comparable a unos auriculares over-ear)

---

## 6. Software — Arquitectura

### 6.1 Stack tecnológico

```
┌───────────────────────────────────────────────────────┐
│                 CAPA DE APLICACIÓN                     │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐  │
│  │ QR-Link  │ │AI Assist │ │ Clock  │ │Telepromp- │  │
│  │ Viewer   │ │(LLM)     │ │& Utils │ │ter        │  │
│  └────┬─────┘ └────┬─────┘ └───┬────┘ └─────┬─────┘  │
│       └─────────────┼──────────┼─────────────┘        │
│                ┌────▼──────────▼────┐                  │
│                │    App Manager     │                  │
│                └────────┬──────────┘                  │
├─────────────────────────┼────────────────────────────┤
│                 CAPA DE SERVICIOS                      │
│  ┌──────────┐ ┌────────▼───┐ ┌─────────┐ ┌────────┐  │
│  │ Display  │ │  Event     │ │  Audio   │ │QR-Link │  │
│  │ Renderer │ │  Bus       │ │ Pipeline │ │Protocol│  │
│  │(Pillow/  │ │ (asyncio)  │ │(STT+TTS)│ │Engine  │  │
│  │ framebuf)│ │            │ │         │ │        │  │
│  └──────────┘ └────────────┘ └─────────┘ └────────┘  │
├───────────────────────────────────────────────────────┤
│                 CAPA DE DRIVERS                        │
│  ┌───────┐ ┌──────┐ ┌─────┐ ┌──────┐ ┌────┐ ┌─────┐ │
│  │SPI    │ │PiCam │ │ BT  │ │WiFi  │ │ALSA│ │MQTT │ │
│  │Display│ │(QR)  │ │     │ │      │ │    │ │/WS  │ │
│  └───────┘ └──────┘ └─────┘ └──────┘ └────┘ └─────┘ │
├───────────────────────────────────────────────────────┤
│            Raspberry Pi OS Lite (Bookworm 64-bit)     │
│            Python 3.11+ / asyncio / systemd           │
└───────────────────────────────────────────────────────┘
```

### 6.2 Estructura del repositorio

```
scouterhud/
├── README.md
├── LICENSE_SOFTWARE              → MIT
├── LICENSE_HARDWARE              → CERN-OHL-S v2
├── PROTOCOL.md                   → Especificación QR-Link Protocol
│
├── docs/
│   ├── TECH_DESIGN.md            → Este documento
│   ├── BUILD_GUIDE.md            → Guía paso a paso con fotos
│   ├── BOM.md                    → Lista de materiales con links
│   ├── WIRING.md                 → Diagramas de conexión
│   ├── OPTICS_GUIDE.md           → Guía de ensamble óptico
│   ├── QR_LINK_GUIDE.md          → Cómo crear QR para tus dispositivos
│   ├── TROUBLESHOOTING.md        → Problemas comunes
│   └── images/
│
├── hardware/
│   ├── 3d-models/
│   │   ├── *.stl                 → Todas las piezas impresas
│   │   └── src/                  → Fuentes FreeCAD/OpenSCAD
│   ├── pcb/                      → KiCad (futuro PCB custom)
│   └── schematics/
│       ├── wiring_diagram.svg
│       └── optics_diagram.svg
│
├── software/
│   ├── scouterhud/
│   │   ├── __init__.py
│   │   ├── main.py               → Entry point, asyncio event loop
│   │   ├── config.py             → Configuration (YAML based)
│   │   │
│   │   ├── display/
│   │   │   ├── __init__.py
│   │   │   ├── backend.py        → ABC DisplayBackend interface
│   │   │   ├── backend_spi.py    → SPI display driver ST7789 (Pi Zero)
│   │   │   ├── backend_desktop.py → Pygame emulator (laptop/PC)
│   │   │   ├── renderer.py       → Layout engine, widget rendering (backend-agnostic)
│   │   │   ├── widgets.py        → Reusable UI components
│   │   │   ├── layouts.py        → Device-type specific layouts
│   │   │   └── fonts/            → Bitmap fonts optimized for small display
│   │   │
│   │   ├── camera/
│   │   │   ├── __init__.py
│   │   │   ├── backend.py        → ABC CameraBackend interface
│   │   │   ├── backend_picamera.py → Pi Camera capture (picamera2)
│   │   │   ├── backend_desktop.py → Webcam/file loader (OpenCV)
│   │   │   └── qr_decoder.py     → QR detection + parsing (pyzbar, backend-agnostic)
│   │   │
│   │   ├── qrlink/
│   │   │   ├── __init__.py
│   │   │   ├── protocol.py       → QR-Link protocol parser/validator
│   │   │   ├── connection.py     → Connection manager (MQTT/HTTP/WS/BLE)
│   │   │   ├── device_registry.py → Known devices cache
│   │   │   ├── transports/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mqtt.py       → MQTT transport
│   │   │   │   ├── http.py       → HTTP/SSE transport
│   │   │   │   ├── websocket.py  → WebSocket transport
│   │   │   │   └── ble.py        → BLE GATT transport
│   │   │   └── schemas/
│   │   │       ├── medical.py    → Medical device data schemas
│   │   │       ├── vehicle.py    → Vehicle data schemas
│   │   │       ├── infra.py      → Infrastructure data schemas
│   │   │       └── generic.py    → Generic key-value schema
│   │   │
│   │   ├── audio/
│   │   │   ├── __init__.py
│   │   │   ├── input.py          → Mic capture
│   │   │   ├── output.py         → Audio playback
│   │   │   └── stt.py            → Speech-to-text (Vosk/Whisper)
│   │   │
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py          → AI agent (Claude API / local)
│   │   │   └── prompts.py        → System prompts
│   │   │
│   │   ├── bluetooth/
│   │   │   ├── __init__.py
│   │   │   └── phone.py          → Phone notifications via BLE
│   │   │
│   │   ├── apps/
│   │   │   ├── __init__.py
│   │   │   ├── home.py           → Home screen (clock, status, notifications)
│   │   │   ├── qrlink_viewer.py  → QR-Link device data viewer
│   │   │   ├── ai_chat.py        → AI assistant interface
│   │   │   ├── teleprompter.py   → Text scroller
│   │   │   └── translator.py     → Live translation
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── power.py          → Battery monitoring
│   │       ├── logger.py         → Centralized logging
│   │       └── network.py        → WiFi/network utilities
│   │
│   ├── tests/
│   │   ├── test_display.py
│   │   ├── test_camera.py
│   │   ├── test_qrlink.py
│   │   ├── test_audio.py
│   │   └── test_protocol.py
│   │
│   ├── scripts/
│   │   ├── setup.sh              → Full automated install
│   │   ├── install_deps.sh       → System dependencies
│   │   ├── generate_qr.py        → CLI tool to generate QR-Link codes
│   │   └── scouterhud.service    → systemd unit file
│   │
│   ├── pyproject.toml
│   └── requirements.txt
│
├── emulator/                     → QR-Link Device Emulator Hub
│   ├── README.md
│   ├── emulator.py               → Main: runs all virtual devices + MQTT broker
│   ├── config.yaml               → Define which devices to emulate
│   ├── devices/
│   │   ├── __init__.py
│   │   ├── base.py               → Base class for virtual devices
│   │   ├── medical_monitor.py    → Respiratory monitor, pulse ox, vitals
│   │   ├── vehicle_obd2.py       → Car OBD-II (RPM, temp, speed, fuel)
│   │   ├── server_infra.py       → AWS instance metrics, costs
│   │   ├── home_thermostat.py    → Home temperature/humidity sensor
│   │   └── industrial_machine.py → Machine cycles, pressure, temp
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── realistic_data.py     → Realistic data patterns with noise
│   │   ├── alert_engine.py       → Random alert/anomaly injection
│   │   └── scenarios.py          → Pre-built scenarios (patient crash, etc.)
│   ├── qr_output/                → Generated QR code images (auto-created)
│   ├── generate_all_qrs.py       → Generates printable QR sheet (PDF)
│   ├── requirements.txt
│   └── docker-compose.yaml       → Optional: Mosquitto + emulator containerized
│
├── qrlink-devices/               → Real device-side implementations (post-MVP)
│   ├── README.md
│   ├── esp32_sensor/             → ESP32 example (Arduino/MicroPython)
│   │   ├── mqtt_publisher.ino
│   │   └── README.md
│   ├── obd2_bridge/              → OBD-II to QR-Link bridge (Python)
│   │   ├── obd2_mqtt.py
│   │   └── README.md
│   └── server_monitor/           → Server metrics publisher
│       ├── server_mqtt.py
│       └── README.md
│
├── companion-app/                → Mobile app (futuro)
│   └── README.md
│
└── media/
    ├── photos/
    ├── renders/
    ├── demo-videos/
    └── logo/
```

### 6.3 OS y configuración base

**Sistema operativo:** Raspberry Pi OS Lite (64-bit, Bookworm)

**Configuraciones en `/boot/firmware/config.txt`:**
```ini
# SPI para display
dtparam=spi=on

# I2C (si se usa OLED alt)
dtparam=i2c_arm=on

# Cámara
start_x=1
gpu_mem=128  # Necesario para Pi Camera

# Reducir consumo - deshabilitar HDMI
hdmi_blanking=2

# Camera LED off (no delatar que estamos escaneando)
disable_camera_led=1
```

### 6.4 Device Emulator Hub

Dado que el protocolo QR-Link es nuevo y no existe en ningún dispositivo real, el proyecto incluye un **emulador multi-dispositivo** que simula el lado "device" del protocolo. Esto es esencial tanto para desarrollo como para demos.

#### Concepto

El emulador es una sola aplicación Python que:
1. Levanta un broker MQTT local (Mosquitto embebido o externo)
2. Instancia N dispositivos virtuales definidos en `config.yaml`
3. Cada dispositivo publica datos realistas periódicamente por MQTT
4. Genera automáticamente los QR codes (imágenes PNG + PDF imprimible)

Corre en cualquier máquina: una laptop, otra Raspberry Pi, o un container Docker. Solo necesita estar en la misma red WiFi que el ScouterHUD.

#### Arquitectura del emulador

```
┌──────────────────────────────────────────────────┐
│              EMULATOR HOST                        │
│         (laptop / RPi / Docker)                   │
│                                                   │
│  ┌────────────────────────────────────────────┐   │
│  │           MQTT Broker (Mosquitto)          │   │
│  │           localhost:1883                    │   │
│  └──────────────────┬─────────────────────────┘   │
│           ┌─────────┼──────────┐                  │
│           │         │          │                  │
│  ┌────────▼──┐ ┌────▼────┐ ┌──▼──────────┐       │
│  │ Medical   │ │ Vehicle │ │ Server      │ ...   │
│  │ Monitor   │ │ OBD-II  │ │ Infra       │       │
│  │           │ │         │ │             │       │
│  │ topic:    │ │ topic:  │ │ topic:      │       │
│  │ med/bed12 │ │ car/001 │ │ srv/i-abc   │       │
│  │ 1x/sec   │ │ 2x/sec  │ │ 1x/5sec    │       │
│  └───────────┘ └─────────┘ └─────────────┘       │
│                                                   │
│  ┌────────────────────────────────────────────┐   │
│  │  QR Generator → qr_output/                 │   │
│  │  medical_monitor_bed12.png                  │   │
│  │  vehicle_obd2_001.png                       │   │
│  │  server_infra_iabc.png                      │   │
│  │  ALL_DEVICES_printable.pdf                  │   │
│  └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘

        WiFi (misma red local)
              │
              ▼
┌──────────────────────┐
│     ScouterHUD       │
│  escanea QR → MQTT   │
│  subscribe → render  │
└──────────────────────┘
```

#### Configuración de dispositivos emulados (`config.yaml`)

```yaml
broker:
  host: "0.0.0.0"
  port: 1883

devices:
  - id: "monitor-bed-12"
    name: "Monitor Respiratorio Cama 12"
    type: "medical.respiratory_monitor"
    topic: "ward3/bed12/vitals"
    auth: "pin"
    pin: "1234"
    refresh_ms: 1000
    scenario: "stable_patient"  # or "gradual_decline", "sudden_alert"
    params:
      spo2_base: 97
      heart_rate_base: 72
      resp_rate_base: 16
      temp_c_base: 36.8

  - id: "car-001"
    name: "Mi Auto - Ford Focus 2018"
    type: "vehicle.obd2"
    topic: "vehicles/car001/obd2"
    auth: "open"
    refresh_ms: 500
    scenario: "city_driving"  # or "highway", "idle", "overheating"
    params:
      rpm_base: 2000
      speed_base: 40
      coolant_temp_base: 88
      fuel_pct_start: 65

  - id: "srv-prod-01"
    name: "Prod Server us-east-1"
    type: "infra.aws_instance"
    topic: "infra/prod/server01"
    auth: "token"
    token: "tok_demo_abc123"
    refresh_ms: 5000
    scenario: "normal_load"  # or "spike", "cost_alert"
    params:
      instance_type: "t3.large"
      monthly_cost_base: 234.56

  - id: "thermo-kitchen"
    name: "Termostato Cocina"
    type: "home.thermostat"
    topic: "home/kitchen/climate"
    auth: "open"
    refresh_ms: 3000
    scenario: "daily_cycle"
    params:
      temp_c_base: 22.0
      humidity_base: 45

  - id: "press-machine-07"
    name: "Prensa Hidráulica #7"
    type: "industrial.pressure_gauge"
    topic: "factory/zone2/press07"
    auth: "pin"
    pin: "5678"
    refresh_ms: 1000
    scenario: "production_cycle"
    params:
      pressure_bar_base: 150
      temp_c_base: 45
      cycle_time_sec: 12
```

#### Generación de datos realistas

Cada dispositivo virtual usa generadores de datos que producen valores creíbles, no simplemente randoms. El sistema modela:

**Señales base con ruido gaussiano:** Los valores fluctúan naturalmente alrededor de una base (ej: SpO2 oscila entre 96-98, no salta de 80 a 100).

**Tendencias temporales:** Escenarios como "gradual_decline" hacen que los valores deriven lentamente en una dirección (paciente empeorando, combustible bajando).

**Correlaciones entre variables:** Si el RPM sube, la temperatura del motor sube con delay. Si SpO2 baja, el heart rate sube como compensación.

**Inyección de alertas:** El `alert_engine` puede disparar eventos aleatorios o programados (desaturación súbita, código DTC en el auto, spike de CPU en el servidor).

**Escenarios pre-armados para demos:**

| Device type | Escenario | Comportamiento |
|------------|-----------|----------------|
| Medical | `stable_patient` | Vitales normales con fluctuación mínima |
| Medical | `gradual_decline` | SpO2 baja 0.1/min, HR sube, genera alerta a los 5 min |
| Medical | `sudden_alert` | Evento de desaturación brusca a tiempo aleatorio |
| Vehicle | `city_driving` | RPM variable 1000-3000, velocidad 0-60, paradas |
| Vehicle | `highway` | RPM estable ~2500, velocidad 100-120 |
| Vehicle | `overheating` | Temperatura sube gradualmente, genera DTC |
| Infra | `normal_load` | CPU 20-40%, memoria estable |
| Infra | `spike` | CPU sube a 95% por 2 min, luego baja |
| Infra | `cost_alert` | Costo mensual excede threshold |
| Home | `daily_cycle` | Temperatura sigue curva día/noche |
| Industrial | `production_cycle` | Ciclos repetitivos con variación |

#### QR printable output

El script `generate_all_qrs.py` lee `config.yaml` y genera:
- Un PNG individual por dispositivo (para pegar en objetos)
- Un PDF con todos los QR en formato imprimible A4 (6 QR por página, con nombre y tipo debajo de cada uno)
- Opcionalmente, tarjetas recortables tipo credencial con QR + nombre + ícono

Esto permite preparar una demo en minutos: imprimir la hoja, recortar, pegar los QR en objetos (o en cartones que representen dispositivos), y listo.

#### Ejecución rápida

```bash
# Setup (una vez)
cd emulator/
pip install -r requirements.txt
docker run -d -p 1883:1883 eclipse-mosquitto  # o instalar local

# Generar QR codes
python generate_all_qrs.py

# Correr emulador (todos los dispositivos)
python emulator.py

# Correr un solo dispositivo para testing
python emulator.py --device monitor-bed-12

# Correr con escenario específico
python emulator.py --device car-001 --scenario overheating
```

#### Transición a dispositivos reales

El emulador produce exactamente los mismos datos en el mismo formato que un dispositivo real lo haría. Esto significa que el ScouterHUD no necesita cambios cuando se pasa de emulador a hardware real. La transición es:

1. **MVP:** Emulador en laptop → ScouterHUD lee QR → ve datos simulados
2. **Post-MVP:** ESP32 real con sensor de temperatura → misma estructura MQTT → ScouterHUD no nota diferencia
3. **Producción:** Dispositivo médico real con adapter QR-Link → mismos datos → mismo display

El directorio `qrlink-devices/` contiene implementaciones de referencia para dispositivos reales (ESP32, OBD-II adapter, server agent) que siguen el mismo schema que el emulador.

### 6.5 Desktop Display Emulator (desarrollo sin hardware)

Para acelerar el desarrollo de software sin depender del Pi Zero 2W ni del display físico, el proyecto incluye un **emulador de display en desktop** que renderiza la misma salida en una ventana pygame en cualquier laptop/PC.

**Principio:** El display driver expone una interfaz abstracta (`DisplayBackend`). En el Pi se usa el driver SPI real; en desktop se usa un backend pygame que renderiza en una ventana de la misma resolución (240x240).

```python
# display/backend.py — interfaz abstracta

class DisplayBackend(ABC):
    @abstractmethod
    def show(self, image: PIL.Image) -> None: ...
    @abstractmethod
    def set_brightness(self, level: int) -> None: ...
    @abstractmethod
    def clear(self) -> None: ...

# display/backend_spi.py — hardware real (Pi Zero)
class SPIBackend(DisplayBackend):
    """ST7789 via SPI. Solo funciona en Raspberry Pi."""
    ...

# display/backend_desktop.py — emulador desktop
class DesktopBackend(DisplayBackend):
    """Renderiza en ventana pygame 240x240 (escalada 3x para visibilidad)."""
    def __init__(self, scale=3):
        pygame.init()
        self.scale = scale
        self.screen = pygame.display.set_mode((240 * scale, 240 * scale))
        pygame.display.set_caption("ScouterHUD — Desktop Emulator")

    def show(self, image: PIL.Image) -> None:
        scaled = image.resize((240 * self.scale, 240 * self.scale), PIL.Image.NEAREST)
        surface = pygame.image.fromstring(scaled.tobytes(), scaled.size, scaled.mode)
        self.screen.blit(surface, (0, 0))
        pygame.display.flip()
```

**Selección automática de backend:**

```python
# config.py
import platform

def get_display_backend():
    if platform.machine().startswith("aarch64") and os.path.exists("/dev/spidev0.0"):
        return SPIBackend()
    else:
        return DesktopBackend()
```

**Emulación de cámara para QR scanning en desktop:**

En desktop, en lugar de capturar frames de la Pi Camera, el emulador permite:
1. **Cargar imagen QR desde archivo:** Simula un scan apuntando a un PNG generado por el emulador de dispositivos.
2. **Usar webcam del laptop:** Si hay webcam disponible, captura frames con OpenCV para escanear QR reales impresos.

```python
# camera/backend_desktop.py
class DesktopCameraBackend:
    """Fallback: carga QR desde archivo o usa webcam con OpenCV."""
    def capture_frame(self) -> PIL.Image:
        if self.use_webcam and self.webcam:
            ret, frame = self.webcam.read()
            return PIL.Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            return PIL.Image.open(self.test_qr_path)
```

**Qué se puede desarrollar en desktop sin hardware:**
- 100% del renderer, layouts y widgets
- 100% del QR-Link protocol parser y connection manager
- 100% de la integración con el Device Emulator Hub (MQTT)
- Pipeline de audio (STT/TTS) con mic/speakers del laptop
- AI agent (Claude API)
- Home screen, apps, navegación

**Qué requiere hardware real:**
- Calibración óptica (beam splitter + lente)
- Validación de brillo y legibilidad see-through
- Consumo de energía y autonomía
- Ergonomía del frame

**Estructura de archivos actualizada:**

```
software/scouterhud/display/
├── __init__.py
├── backend.py              → ABC DisplayBackend
├── backend_spi.py          → ST7789 SPI (Pi Zero)
├── backend_desktop.py      → Pygame emulator (laptop)
├── renderer.py             → Layout engine (backend-agnostic)
├── widgets.py              → UI components
├── layouts.py              → Device-type layouts
└── fonts/

software/scouterhud/camera/
├── __init__.py
├── backend.py              → ABC CameraBackend
├── backend_picamera.py     → Pi Camera (Pi Zero)
├── backend_desktop.py      → Webcam / file loader (laptop)
└── qr_decoder.py           → QR detection (pyzbar, backend-agnostic)
```

### 6.6 QR-Link Engine — Implementación

**Flujo principal (asyncio):**

```python
# Pseudocode del QR-Link engine loop

async def qrlink_scan_mode():
    """Activate camera, scan for QR, connect to device."""
    camera = PiCamera2(resolution=(640, 480))

    while scanning:
        frame = await camera.capture_async()
        qr_data = decode_qr(frame)  # pyzbar

        if qr_data:
            device = QRLinkProtocol.parse(qr_data)
            if device.is_valid():
                connection = await ConnectionManager.connect(device)
                await switch_to_viewer(device, connection)
                return

async def device_viewer(device, connection):
    """Receive live data and render on display."""
    layout = LayoutEngine.get_layout(device.type)

    async for data in connection.stream():
        frame = layout.render(data)
        display.show(frame)
```

**Generador de QR codes (herramienta CLI):**

El repo incluye `scripts/generate_qr.py` que genera QR codes listos para imprimir:

```bash
# Generar QR para un sensor de temperatura
python generate_qr.py \
  --name "Sensor Cocina" \
  --type "home.temperature_sensor" \
  --proto mqtt \
  --endpoint "192.168.1.100:1883" \
  --topic "home/kitchen/temp" \
  --output qr_sensor_cocina.png
```

### 6.7 Pipeline de IA

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ MIC      │───►│ VAD      │───►│ STT      │───►│ LLM      │
│ capture  │    │ (silero) │    │ (Vosk/   │    │ (Claude  │
│ USB      │    │          │    │  Whisper  │    │  API)    │
│          │    │          │    │  API)     │    │          │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                     │
┌──────────┐    ┌──────────┐                         │
│ DISPLAY  │◄───│ TTS      │◄────────────────────────┘
│ render   │    │ (Piper / │
│ (beam    │    │  espeak)  │
│ splitter)│    └──────────┘
└──────────┘         │
                     ▼
               ┌──────────┐
               │ EARPIECE │
               └──────────┘
```

**Opciones de STT:**

| Opción | Latencia en Pi Zero | Calidad | Offline |
|--------|-------------------|---------|---------|
| Vosk (modelo small-es) | 1-3s | Buena para comandos | Sí |
| Whisper tiny (local) | 5-10s | Aceptable | Sí |
| Whisper API (cloud) | 1-2s | Excelente | No |
| Google STT API | 0.5-1s | Excelente | No |

**Recomendación:** Vosk offline para wake words y comandos ("escanear", "hora", "cerrar"). Whisper API para transcripción larga cuando hay WiFi.

**Opciones de TTS:**

| Opción | Latencia en Pi Zero | Calidad | Offline |
|--------|-------------------|---------|---------|
| espeak-ng | Instantáneo | Robótica | Sí |
| Piper TTS (es_ES) | 2-4s | Natural | Sí |
| Google TTS API | 0.5-1s | Excelente | No |

**Recomendación:** Piper TTS offline con fallback a cloud.

---

## 7. Roadmap de desarrollo

### Phase 0 — Proof of Concept: Óptica (Semana 1-2)

**Objetivo:** Validar que el sistema see-through funciona y es legible.

- [ ] Soldar headers al Pi Zero 2W
- [ ] Conectar display ST7789 por SPI
- [ ] Instalar RPi OS Lite + habilitar SPI
- [ ] Correr script de test (texto blanco sobre fondo negro)
- [ ] Experimentar con beam splitter (acrílico de caja de CD)
- [ ] Probar diferentes lentes asféricas entre display y splitter
- [ ] Validar: ¿se lee texto Y se ve el mundo real simultáneamente?
- [ ] Documentar configuración óptica ganadora con fotos

**Criterio de éxito:** Leer texto de 14px en el display a través del beam splitter mientras se ve el entorno real detrás, por 5+ minutos sin fatiga.

### Phase 1 — QR-Link MVP (Semana 3-5)

**Objetivo:** Escanear QR y mostrar datos en vivo de un dispositivo emulado.

- [ ] **Emulador primero:** Implementar Device Emulator Hub
  - [ ] Base device class + realistic data generators
  - [ ] Medical monitor emulator (escenario stable_patient)
  - [ ] Vehicle OBD-II emulator (escenario city_driving)
  - [ ] Server infra emulator (escenario normal_load)
  - [ ] `config.yaml` con 3-5 dispositivos de demo
  - [ ] `generate_all_qrs.py` → PDF imprimible con QR codes
  - [ ] Docker compose con Mosquitto + emulador
- [ ] **Desktop emulator:** Implementar DisplayBackend ABC + DesktopBackend (pygame)
- [ ] **Desktop emulator:** Implementar CameraBackend ABC + DesktopCameraBackend (webcam/archivo)
- [ ] Implementar QR scanning con pyzbar (backend-agnostic)
- [ ] Implementar QR-Link protocol parser (formato URL compacto + metadata lookup)
- [ ] Implementar MQTT transport en ScouterHUD
- [ ] Implementar PIN auth (Nivel 1)
- [ ] Renderizar datos del emulador en el desktop emulator (pygame)
- [ ] Validar flujo completo en desktop: scan QR → connect MQTT → render datos
- [ ] Conectar Pi Camera, validar captura en hardware real
- [ ] Implementar SPIBackend para display real en Pi Zero
- [ ] **Test de memoria temprano:** Medir consumo de RAM con picamera2 + Vosk + paho-mqtt + Pillow corriendo simultáneamente en Pi Zero 2W (512MB). Establecer baseline y límites.
- [ ] Primer print 3D del housing óptico

### Phase 2 — Software completo (Semana 6-8)

- [ ] Display renderer con layout system y widgets
- [ ] Layouts automáticos por device type
- [ ] Audio: USB sound card + mic + auricular
- [ ] Vosk STT para comandos de voz ("escanear", "hora", "cerrar")
- [ ] Home screen (reloj, batería, estado WiFi)
- [ ] generate_qr.py CLI tool
- [ ] Segundo transport: HTTP/SSE
- [ ] Primer print 3D del frame completo (vincha)

### Phase 3 — AI + Polish (Semana 9-12)

- [ ] Pipeline STT → Claude API → TTS → Display
- [ ] AI puede interpretar datos del dispositivo conectado
  ("¿cómo están los signos vitales?" con datos live como contexto)
- [ ] Diseño 3D final (iterar ergonomía 2-3 veces)
- [ ] BUILD_GUIDE.md completo con fotos paso a paso
- [ ] OPTICS_GUIDE.md
- [ ] QR_LINK_GUIDE.md con ejemplos
- [ ] Script setup.sh automatizado
- [ ] Video demo para publicación

### Phase 4 — Publish & Community (Semana 13-14)

- [ ] README pulido (GIF hero, badges, screenshots)
- [ ] Publicar en GitHub
- [ ] Publicar en Hackaday.io
- [ ] Serie de posts en LinkedIn (ver sección 9)
- [ ] Post en Reddit (r/raspberry_pi, r/DIY, r/AugmentedReality, r/IoT)
- [ ] Video YouTube (5-10 min)

### Phase 5+ — Expansion (Futuro)

- [ ] Example devices: ESP32 sensor real, OBD-II bridge
- [ ] Companion app móvil (Flutter) para notificaciones
- [ ] Transports adicionales: WebSocket, BLE
- [ ] PCB custom (KiCad)
- [ ] Upgrade a Pi CM4 / Pi 5 para AI local (Whisper + small LLM)
- [ ] Conducción ósea para audio
- [ ] QR-Link v2: NFC como alternativa al QR visual
- [ ] QR-Link device registry web (directorio público de devices)

---

## 8. Riesgos y mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|------------|
| Beam splitter con mala relación reflejo/transparencia | Alto | Media | Probar múltiples materiales en Phase 0, comprar muestras |
| Display no suficientemente brillante para see-through | Alto | Media | Usar TFT IPS de alto brillo, ajustar PWM al máximo, testear en diferentes condiciones de luz |
| Pi Camera lenta para decodificar QR | Medio | Baja | 640x480 con pyzbar es rápido (~100ms). Fallback: pre-crop de ROI |
| Pi Zero 2W lento para STT local | Alto | Alta | Usar Vosk (más liviano) para comandos, API para queries largas |
| Fatiga visual tras uso prolongado | Medio | Alta | Iterar óptica, permitir ajuste de brillo/posición, documentar límites |
| Calentamiento del Pi en enclosure | Medio | Media | Ventilas en diseño 3D, disipador de cobre adhesivo |
| Latencia en pipeline AI | Medio | Media | Streaming responses, indicador "pensando", feedback auditivo |
| Seguridad QR-Link (datos sensibles) | Alto | Baja (MVP) | Documentar riesgos, implementar auth en Phase 5 |

---

## 9. Estrategia de posicionamiento público

### 9.1 Narrative del proyecto

**Tagline:** "Scan any device. See its data. Open source AR for $60."

**Story alternativo:** "What if any device could show you its data just by looking at it?"

El QR-Link protocol es el diferenciador principal. No es "otro proyecto de smart glasses DIY" — es un estándar abierto para que cualquier dispositivo pueda comunicarse con un wearable visual. Los lentes son el hardware; QR-Link es la innovación.

### 9.2 Contenido a crear

**Serie LinkedIn (5 posts):**
1. "Estoy construyendo un scouter de Dragon Ball Z que lee dispositivos IoT" (hook + concepto + render)
2. "¿Y si pudieras ver los datos de cualquier dispositivo solo mirándolo?" (demo del QR-Link protocol)
3. "Primer prototipo funcional por menos de $60" (video demo, BOM)
4. "Diseñé un protocolo abierto para que cualquier dispositivo hable con un wearable" (technical deep dive)
5. "El repo es público. Construílo vos también." (GitHub link + call to action)

**GitHub README con:**
- GIF hero: escanear QR → datos aparecen en el display
- "Build it in a weekend" promise
- BOM con links y precios
- Badges: CI, license, stars, contributors

**Otras plataformas:**
- Hackaday.io (project page con build log)
- YouTube (5-10 min build + QR-Link demo)
- Reddit: r/raspberry_pi, r/DIY, r/AugmentedReality, r/IoT, r/homeautomation
- Hacker News (Show HN)

### 9.3 Diferenciación

| Aspecto | DIY existentes | Brilliant Monocle | ScouterHUD |
|---------|---------------|-------------------|------------|
| Precio | $30-80 | $349 | $50-68 |
| See-through | Raro | Sí (micro OLED) | Sí (beam splitter) |
| Cámara | Raro | Sí (5MP) | Sí (5MP, QR scan) |
| QR-Link protocol | No | No | **Sí (innovación)** |
| Device discovery | No | No | **Sí (escaneo visual)** |
| AI integrado | No | Sí (arGPT) | Sí (Claude + Vosk) |
| Documentación | Fragmentada | Buena | Excelente (objetivo) |
| Reproducibilidad | Difícil | Comprar ($349) | Fácil (BOM + guía) |

---

## 10. Referencias y recursos

### Proyectos inspiradores
- **"Zero" AR Glasses** por Miroslav Kotalík — Pi Zero, lentes custom, 60 FPS SPI
- **Brilliant Labs Monocle/Halo** — AR open source comercial, micro OLED
- **Kian Pipalia AR Glasses** — Pi Zero 2W, TFT 0.96", frame impreso 3D
- **VisorWare** — Software Python3 para smart glasses (GitHub: 1zc/VisorWare)
- **MIT µ-HUD** — Paper original de micro HUD con beam splitter (1990s)

### Librerías clave
- `picamera2` — Pi Camera capture (official)
- `pyzbar` — QR/barcode decoding
- `luma.lcd` / `luma.oled` — Display drivers
- `Pillow` — Image rendering
- `paho-mqtt` — MQTT client
- `aiohttp` — Async HTTP client
- `websockets` — WebSocket client
- `vosk` — Offline STT
- `piper-tts` — Offline TTS
- `anthropic` — Claude API SDK
- `silero-vad` — Voice Activity Detection
- `bleak` — BLE for Python
- `qrcode` — QR code generation (for generate_qr.py)

### Datasheets
- Raspberry Pi Zero 2W Product Brief
- ST7789 TFT Display Controller
- SSD1306 OLED Controller
- OV5647 Camera Sensor (Pi Camera v1)
- TP4056 Li-ion Battery Charger
- MT3608 DC-DC Boost Converter
