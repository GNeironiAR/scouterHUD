# ScouterGauntlet — Open Source Wrist Input Device for ScouterHUD

## Technical Design Document v0.1

**Project Codename:** ScouterGauntlet  
**Companion to:** ScouterHUD  
**Author:** Ger  
**Date:** February 2026  
**License:** MIT (Software) / CERN-OHL-S v2 (Hardware)  
**Status:** Concepto / Diseño

---

## 1. Vision & Scope

### 1.1 El problema

ScouterHUD tiene dos canales de input: voz y escaneo de QR. Pero hay escenarios donde la voz no sirve:

- **Seguridad:** No podés decir un TOTP o PIN en voz alta
- **Silencio:** Reuniones, hospitales, bibliotecas, transporte público
- **Ruido:** Ambientes industriales donde el mic no capta bien
- **Precisión:** Navegar menús, seleccionar opciones, confirmar/cancelar
- **Privacidad:** No querés que otros sepan qué estás haciendo

Un teclado convencional no es opción — el usuario tiene las manos ocupadas o en movimiento. Se necesita un input device que se opere con una sola mano, casi sin mirar, y que sea discreto.

### 1.2 Qué es ScouterGauntlet

Un brazalete de antebrazo basado en ESP32 con pads táctiles capacitivos que permite al usuario interactuar con el ScouterHUD mediante toques y combinaciones simples. Se comunica por BLE con el ScouterHUD.

Inspirado en el wrist computer del Predator: compacto, funcional, operable sin mirar.

### 1.3 Qué NO es

- No es un teclado QWERTY miniaturizado
- No es un smartwatch (no tiene pantalla propia en el MVP)
- No es un reemplazo de voz — es un complemento
- No requiere mirar el brazalete para operar (feedback háptico + audio)

### 1.4 Principios de diseño

1. **Operable a ciegas:** El usuario aprende las posiciones por tacto, no por vista
2. **Mínimo cognitivo:** Máximo 5-6 pads, combinaciones intuitivas
3. **Una sola mano:** Operado con los dedos de la mano contraria o con la misma mano (thumb-reach)
4. **Discreto:** Parece un brazalete fitness, no un prop de ciencia ficción
5. **Bajo costo:** < $15 USD adicionales al ScouterHUD

---

## 2. Sistema de input

### 2.1 Filosofía: Chord-based minimal input

En vez de muchas teclas, usamos pocos pads con combinaciones (chords). Con 5 pads capacitivos se pueden generar 31 combinaciones únicas (2^5 - 1). Eso cubre el alfabeto completo, números, y comandos de navegación.

Pero para el MVP no necesitamos 31 combinaciones. Necesitamos resolver estos modos:

### 2.2 Modos de operación

**Modo 1 — Navegación (default)**

5 pads con funciones directas, sin combinaciones:

```
┌─────────────────────────────────────────┐
│           ANTEBRAZO (vista superior)      │
│                                          │
│   [PAD 1]  [PAD 2]  [PAD 3]  [PAD 4]   │
│    ◄ LEFT   ▲ UP    ▼ DOWN   ► RIGHT    │
│                                          │
│              [PAD 5]                     │
│              CONFIRM                     │
│           (más grande)                   │
│                                          │
│   Gesto: hold PAD 1+4 = CANCEL/BACK     │
│   Gesto: double-tap PAD 5 = HOME        │
│   Gesto: hold PAD 5 (2s) = VOICE MODE   │
│                                          │
└─────────────────────────────────────────┘
```

Esto cubre: navegar menús en el HUD, seleccionar opciones, confirmar PIN (ver dígitos en pantalla, navegar, confirmar), volver atrás.

**Modo 2 — Texto numérico (para PIN/TOTP)**

Activado al entrar en un campo numérico. Los pads cambian de función:

```
PAD 1 (◄): Decrementar dígito (-1)
PAD 2 (▲): Mover al dígito anterior
PAD 3 (▼): Mover al siguiente dígito
PAD 4 (►): Incrementar dígito (+1)
PAD 5:     Confirmar número completo

Display del HUD muestra:
┌──────────────┐
│  PIN: [3] 7 _ _ │
│        ▲        │
│  ◄(-1)   (+1)►  │
└──────────────┘
```

El usuario ve los dígitos en el HUD, navega con izquierda/derecha, sube/baja el valor con arriba/abajo, y confirma. Nunca dice nada en voz alta.

**Modo 3 — Texto completo (chord input)**

Para escribir texto libre (búsquedas, mensajes cortos). Usa chording similar al TapStrap:

```
Vocales (un solo pad):
  PAD 1 = A
  PAD 2 = E
  PAD 3 = I
  PAD 4 = O
  PAD 5 = U

Consonantes frecuentes (dos pads adyacentes):
  PAD 1+2 = N    PAD 2+3 = T    PAD 3+4 = L    PAD 4+5 = S

Consonantes (dos pads no adyacentes):
  PAD 1+3 = R    PAD 1+4 = D    PAD 1+5 = C
  PAD 2+4 = M    PAD 2+5 = P    PAD 3+5 = B

Más consonantes (tres pads):
  PAD 1+2+3 = G    PAD 2+3+4 = F    PAD 3+4+5 = H
  PAD 1+2+4 = V    PAD 1+3+4 = J    PAD 2+4+5 = Q
  PAD 1+2+5 = K    PAD 1+3+5 = W    PAD 2+3+5 = X
  PAD 1+4+5 = Y    PAD 1+2+3+4 = Z

Controles especiales:
  PAD 1+2+3+4+5 (todos) = ESPACIO
  Hold PAD 5 (1s) = BORRAR último carácter
  Double-tap PAD 5 = ENVIAR texto
  Hold PAD 1+4 = CANCELAR y salir del modo texto
```

**Nota:** El chording es un skill que se aprende. El MVP prioriza el Modo 1 (navegación) y Modo 2 (numérico). El Modo 3 es para usuarios avanzados, post-MVP.

**Modo 4 — Quick actions (gestures)**

Gestos rápidos sin entrar a ningún menú:

| Gesto | Acción |
|-------|--------|
| Double-tap PAD 5 | Home / toggle última app |
| Hold PAD 5 (2s) | Activar/desactivar modo voz |
| Hold PAD 1+4 (1s) | Cancelar / back |
| Triple-tap PAD 5 | Activar QR scan |
| Swipe PAD 1→4 (secuencial) | Siguiente dispositivo QR-Link |
| Swipe PAD 4→1 (secuencial) | Dispositivo QR-Link anterior |
| Hold todos (3s) | Lock/unlock ScouterHUD |

### 2.3 Feedback al usuario

El usuario NO mira el brazalete. El feedback viene de:

**Visual (en el HUD):**
- Indicador de modo actual (NAV / NUM / TXT)
- Highlight del dígito/carácter seleccionado
- Preview del texto escrito
- Confirmación visual de cada input

**Háptico (en el brazalete):**
- Micro motor de vibración en el brazalete
- Pulso corto (50ms) = input recibido
- Pulso doble = modo cambiado
- Pulso largo (200ms) = error / input inválido

**Auditivo (en el earpiece del HUD):**
- Click sutil por cada input (opcional, configurable)
- TTS para confirmar acciones importantes ("PIN aceptado")

---

## 3. Hardware

### 3.1 Diagrama de bloques

```
┌─────────────────────────────────────────────┐
│              SCOUTERGAUNTLET                 │
│           (brazalete antebrazo)              │
│                                              │
│  ┌───────────────────────────────────────┐   │
│  │  5x CAPACITIVE TOUCH PADS            │   │
│  │  (copper PCB pads + overlay)          │   │
│  └──────────────┬────────────────────────┘   │
│                 │ GPIO touch pins             │
│           ┌─────▼──────┐                     │
│           │  ESP32-S3  │                     │
│           │  (or C3)   │                     │
│           │            │──► BLE ──► ScouterHUD
│           │  ┌──────┐  │                     │
│           │  │Flash │  │                     │
│           └──┤      ├──┘                     │
│              └──────┘                        │
│  ┌───────────┐    ┌────────────────┐         │
│  │ VIBRATION │    │ LiPo BATTERY   │         │
│  │ MOTOR     │    │ 250-500mAh     │         │
│  └───────────┘    │ + TP4056       │         │
│                   │ + USB-C charge │         │
│                   └────────────────┘         │
└─────────────────────────────────────────────┘
```

### 3.2 Bill of Materials

| # | Componente | Modelo recomendado | Precio aprox. |
|---|-----------|-------------------|---------------|
| 1 | MCU | ESP32-S3 Mini (o ESP32-C3) | $3-5 |
| 2 | Touch pads | Copper pads en PCB custom (5 zonas) | $2-3 (fabricación PCB) |
| 3 | Touch pads ALT | Papel aluminio + cinta adhesiva | $0 (prototipo) |
| 4 | Motor vibración | Micro motor coin 10mm 3V | $0.50-1 |
| 5 | Batería | LiPo 3.7V 400mAh (503030) | $2-3 |
| 6 | Cargador | TP4056 módulo micro (o USB-C) | $0.50-1 |
| 7 | MOSFET | 2N7000 (para controlar motor vibración) | $0.10 |
| 8 | Varios | Resistencias, capacitores, switch | $1 |
| 9 | PCB | PCB custom 2-layer (JLCPCB/PCBWay) | $2-5 (por 5 unidades) |
| 10 | Frame | Impresión 3D (PETG flexible) o correa nylon | $2-3 |
| 11 | Overlay | Film protector + marcas táctiles en relieve | $1 |

**Costo total estimado:** $12-20 USD

### 3.3 ESP32-S3 — Selección del MCU

El ESP32-S3 es ideal porque:

- 10 pines de touch capacitivo nativos (solo necesitamos 5)
- BLE 5.0 nativo (bajo consumo)
- WiFi (para OTA firmware updates)
- Deep sleep: ~10µA (batería dura semanas en standby)
- Ultra bajo costo (~$3 el módulo)
- Soporte Arduino + MicroPython + ESP-IDF

**Alternativa más barata:** ESP32-C3 (~$2) tiene BLE pero NO tiene touch capacitivo nativo. Se necesitaría un IC externo (MPR121) o medir capacitancia por software. Más complejo pero viable.

### 3.4 Touch pads — Diseño

**PCB custom con pads de cobre:**

```
┌─────────────────────────────────────────────────────┐
│                    PCB TOP VIEW                      │
│            (curvo, se adapta al antebrazo)           │
│                                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ PAD 1  │ │ PAD 2  │ │ PAD 3  │ │ PAD 4  │       │
│  │ 12x15mm│ │ 12x15mm│ │ 12x15mm│ │ 12x15mm│       │
│  │ GPIO1  │ │ GPIO2  │ │ GPIO3  │ │ GPIO4  │       │
│  └────────┘ └────────┘ └────────┘ └────────┘       │
│                                                      │
│           ┌──────────────────────┐                   │
│           │       PAD 5         │                   │
│           │      18x20mm        │                   │
│           │      GPIO5          │                   │
│           │    (CONFIRM)        │                   │
│           └──────────────────────┘                   │
│                                                      │
│  [ESP32-S3]  [TP4056]  [MOTOR]  [LiPo connector]   │
│  (underside) (underside)                             │
└─────────────────────────────────────────────────────┘

Dimensiones totales: ~70mm x 45mm
```

**Separación entre pads:** Mínimo 3mm (ground guard ring entre pads para evitar cross-talk).

**Overlay:** Un film plástico de 0.3-0.5mm sobre los pads protege el cobre y permite agregar marcas táctiles en relieve (dots o ridges) para ubicar los pads sin mirar. La sensibilidad capacitiva funciona a través del film.

**Prototipo rápido:** Para las primeras pruebas, se puede usar papel aluminio pegado con cinta aislante sobre un cartón, conectado con cables al ESP32 dev board. Funciona perfectamente para validar el concepto.

### 3.5 Alimentación

| Estado | Consumo | Notas |
|--------|---------|-------|
| Deep sleep (BLE advertising) | ~0.5 mA | Esperando conexión |
| Active (BLE connected, idle) | ~15 mA | Conectado, sin toques |
| Active (touch + BLE TX + haptic) | ~40 mA | Pico durante uso |

**Autonomía con LiPo 400mAh:**
- Uso activo continuo: ~10 horas
- Uso intermitente (2 hrs activo / 22 hrs sleep): **~5-7 días**
- Standby puro: **~30 días**

---

## 4. Software

### 4.1 Firmware del Gauntlet (ESP32)

**Plataforma:** Arduino framework o ESP-IDF

```
gauntlet-firmware/
├── src/
│   ├── main.cpp                → Setup + main loop
│   ├── touch/
│   │   ├── touch_driver.h      → ESP32 capacitive touch config
│   │   ├── touch_driver.cpp
│   │   ├── chord_detector.h    → Chord detection (multi-pad combos)
│   │   └── chord_detector.cpp
│   ├── ble/
│   │   ├── ble_hid.h           → BLE HID profile (keyboard emulation)
│   │   ├── ble_hid.cpp
│   │   ├── ble_custom.h        → Custom BLE service for ScouterHUD
│   │   └── ble_custom.cpp
│   ├── haptic/
│   │   ├── haptic.h            → Vibration motor patterns
│   │   └── haptic.cpp
│   ├── power/
│   │   ├── power_mgmt.h        → Deep sleep, wake on touch
│   │   └── power_mgmt.cpp
│   └── config.h                → Pin definitions, thresholds, timings
├── platformio.ini
└── README.md
```

### 4.2 Protocolo BLE entre Gauntlet y ScouterHUD

**Opción A — BLE HID (Keyboard emulation):**
El Gauntlet se presenta como un teclado BLE estándar. Cada chord se mapea a una tecla o combinación. Funciona con cualquier dispositivo BLE, no solo ScouterHUD.

- Ventaja: Compatible con cualquier dispositivo (celular, PC, tablet)
- Desventaja: Limitado a keycodes estándar, no envía metadata

**Opción B — Custom BLE GATT Service (recomendado):**
Servicio BLE custom que envía eventos estructurados al ScouterHUD.

```
BLE Service UUID: 0xSCOT (custom)

Characteristics:
├── input_event (notify)
│   → {type: "tap|chord|gesture", pads: [1,5], mode: "nav", timestamp: ms}
│
├── mode_status (read/write)
│   → {current_mode: "nav|num|text", hud_connected: true}
│
├── haptic_command (write)
│   → {pattern: "short|double|long|error", intensity: 0-100}
│
└── battery_level (read/notify)
    → {level_pct: 85, charging: false}
```

**Recomendación:** Implementar AMBOS. BLE HID como fallback universal, Custom GATT como primario cuando está conectado al ScouterHUD. El ScouterHUD usa el custom service para funcionalidad completa; si se conecta a un celular, funciona como teclado BLE básico.

### 4.3 Integración con ScouterHUD (lado Pi)

Nuevo módulo en el software del ScouterHUD:

```
software/scouterhud/input/
├── __init__.py
├── gauntlet.py          → BLE client, recibe eventos del Gauntlet
├── input_manager.py     → Unifica input (voz + gauntlet + QR)
├── chord_map.py         → Mapeo de chords a caracteres/acciones
└── modes/
    ├── __init__.py
    ├── navigation.py    → Modo navegación (D-pad virtual)
    ├── numeric.py       → Modo numérico (entry de PIN/TOTP)
    └── text.py          → Modo texto (chording completo)
```

**Flujo de un PIN entry:**

```
1. ScouterHUD entra en pantalla de auth (PIN requerido por QR-Link)
2. ScouterHUD envía a Gauntlet via BLE: mode_change → "num"
3. Gauntlet vibra doble (confirma cambio de modo)
4. HUD muestra: PIN: [_] _ _ _
5. Usuario toca PAD 4 (►): dígito incrementa → PIN: [1] _ _ _
6. Usuario toca PAD 4 de nuevo: → PIN: [2] _ _ _
7. HUD feedback visual por cada toque
8. Gauntlet vibra corto por cada toque
9. Usuario toca PAD 3 (▼): mueve al siguiente dígito → PIN: 2 [_] _ _
10. Repite para los 4 dígitos
11. Usuario toca PAD 5 (CONFIRM): envía PIN
12. Si correcto: HUD muestra datos, Gauntlet vibra OK
13. Si incorrecto: HUD muestra error, Gauntlet vibra largo (error)
14. Gauntlet vuelve a modo NAV automáticamente
```

---

## 5. Diseño mecánico

### 5.1 Form factor

```
Vista lateral del antebrazo con ScouterGauntlet:

         ┌───────────────────────┐
         │    PCB + PADS        │ ← superficie de interacción
         │   (cara exterior)     │    accesible con la otra mano
    ─────┤                      ├─────
    strap│  ┌──────────────┐    │strap
    (vel-│  │ ESP32 + LiPo │    │(vel-
    cro) │  │ (cara interna│    │cro)
    ─────┤  │  contra piel)│    ├─────
         │  └──────────────┘    │
         └───────────────────────┘
              ANTEBRAZO
         (terço medio-distal)

Posición: En el antebrazo de la mano NO dominante
(si sos diestro, va en el antebrazo izquierdo,
así usás la mano derecha para tocar los pads)
```

### 5.2 Piezas impresas 3D

```
hardware/gauntlet/3d-models/
├── gauntlet_base.stl        → Base que sostiene PCB (curva al antebrazo)
├── gauntlet_cover.stl       → Tapa protectora con ventanas para pads
├── gauntlet_strap_clip.stl  → Clips para correa de velcro (×2)
└── src/                     → Fuentes FreeCAD/OpenSCAD
```

**Material:** TPU flexible para la base (se adapta a la curvatura del brazo) o PETG rígido con padding de espuma.

### 5.3 Ergonomía

- **Peso total:** ~25-35g (imperceptible)
- **Ancho:** ~45mm (no interfiere con movimiento de muñeca)
- **Posición de pads:** Los 4 pads superiores están en línea, alcanzables con barrido del pulgar o dedos
- **PAD 5 (confirm):** Más grande y más abajo, accesible con el pulgar de forma natural
- **Marcas táctiles:** Dot en relieve en PAD 2 y PAD 5 para orientación sin mirar

---

## 6. Roadmap

### Phase G0 — Proof of Concept (Semana 1-2)

**Objetivo:** Validar touch capacitivo y BLE con ESP32 dev board.

- [ ] ESP32-S3 dev board en breadboard
- [ ] 5 pads de papel aluminio conectados a touch pins
- [ ] Script Arduino: detectar toques individuales y chords
- [ ] BLE: enviar eventos a un celular (app BLE scanner)
- [ ] Motor de vibración con MOSFET
- [ ] Medir consumo en diferentes estados

**Criterio de éxito:** Detectar toques y chords de 2-3 pads con <50ms de latencia y 0 false positives en 100 intentos.

### Phase G1 — Integración con ScouterHUD (Semana 3-4)

- [ ] Custom BLE GATT service en el Gauntlet
- [ ] Módulo `input/gauntlet.py` en ScouterHUD
- [ ] Modo navegación funcionando (navegar menú del HUD)
- [ ] Modo numérico funcionando (ingresar PIN en QR-Link auth)
- [ ] Feedback háptico sincronizado con HUD
- [ ] Primer prototipo físico (PCB de prototipo o perfboard)

### Phase G2 — PCB custom + enclosure (Semana 5-7)

- [ ] Diseño de PCB en KiCad (ESP32-S3 + pads + motor + LiPo)
- [ ] Fabricación PCB (JLCPCB)
- [ ] Diseño 3D del enclosure
- [ ] Assembly y testing
- [ ] BLE HID mode (fallback como teclado universal)
- [ ] Modo texto (chording) — básico

### Phase G3 — Polish + Docs (Semana 8-9)

- [ ] Firmware OTA updates via WiFi
- [ ] Deep sleep optimizado (wake on touch)
- [ ] Calibración automática de touch thresholds
- [ ] BUILD_GUIDE.md con fotos
- [ ] Chord map reference card (PDF imprimible)
- [ ] Integrar en el repo principal de ScouterHUD

---

## 7. Relación con ScouterHUD

### 7.1 Repositorio

ScouterGauntlet vive dentro del repo principal de ScouterHUD:

```
scouterhud/
├── ...todo lo del HUD...
├── gauntlet/
│   ├── firmware/             → Código ESP32 (PlatformIO)
│   ├── hardware/
│   │   ├── 3d-models/        → STL del enclosure
│   │   ├── pcb/              → KiCad files
│   │   └── schematics/
│   ├── docs/
│   │   ├── BUILD_GUIDE.md
│   │   ├── CHORD_MAP.md      → Referencia de chords
│   │   └── PAIRING.md        → Cómo emparejar con ScouterHUD
│   └── README.md
```

### 7.2 Input unificado

El ScouterHUD tiene un `InputManager` que abstrae la fuente de input:

```python
# Pseudocode del input unificado

class InputManager:
    """Unify all input sources into a single event stream."""

    sources = [
        VoiceInput(),       # Mic → STT → commands
        GauntletInput(),    # BLE → touch events
        QRScanInput(),      # Camera → QR detection
    ]

    async def get_next_event(self):
        # Returns the next input event from ANY source
        # Priority: Gauntlet (immediate) > QR (scan trigger) > Voice
        ...

# Las apps del HUD no saben ni les importa de dónde viene el input
class PinEntryApp:
    async def run(self, input_mgr, display):
        display.show("Enter PIN: [_]___")
        pin = ""
        while len(pin) < 4:
            event = await input_mgr.get_next_event()
            if event.type == "digit_change":
                # Could come from gauntlet pad OR voice "tres"
                ...
```

### 7.3 Independencia

El ScouterGauntlet es un accesorio OPCIONAL del ScouterHUD. El HUD funciona completamente sin él (solo con voz y QR). Pero al conectar el Gauntlet, se desbloquean:

- Input silencioso para PINs y TOTPs
- Navegación rápida de menús
- Escritura de texto sin hablar
- Control en ambientes ruidosos
- Experiencia "manos libres" completa combinado con voz

Además, gracias al modo BLE HID, el Gauntlet funciona independientemente como teclado/controller BLE para cualquier dispositivo (celular, tablet, PC, VR headset).

---

## 8. Diferenciación vs productos existentes

| Aspecto | TapXR ($199) | TapStrap 2 ($149) | Meta sEMG (no disponible) | ScouterGauntlet |
|---------|-------------|-------------------|---------------------------|-----------------|
| Precio | $199 | $149 | N/A | $12-20 |
| Form factor | Pulsera muñeca | Anillos en dedos | Pulsera muñeca | Brazalete antebrazo |
| Input method | Finger taps en superficie | Finger chords en superficie | EMG muscular | Capacitive pads directos |
| Requiere superficie | Sí | Sí | No | No |
| Open source | No | No | No | Sí (100%) |
| Diseñado para AR | Parcial | Parcial | Sí (Meta Orion) | Sí (ScouterHUD) |
| BLE HID universal | Sí | Sí | No info | Sí |
| Feedback háptico | Sí | Sí | Sí | Sí |

**Ventaja clave del ScouterGauntlet:** No requiere apoyar la mano en ninguna superficie. Los pads están en el brazalete, los tocás directamente con la otra mano. Esto lo hace usable caminando, parado, acostado — en cualquier posición.

---

## 9. Futuro

### 9.1 Evoluciones posibles

**Mini display (post-MVP):** Agregar un OLED 0.42" (72x40) al Gauntlet que muestre el dígito actual o un indicador de modo. No reemplaza al HUD, es un glanceable backup.

**IMU (acelerómetro/giroscopio):** Agregar MPU6050 para detectar gestos de muñeca: flip para activar, tilt para scroll, shake para cancelar. El ESP32-S3 tiene capacidad de sobra.

**Touch slider:** Reemplazar los 4 pads superiores por un slider lineal capacitivo continuo. Permite scroll fluido y selección analógica.

**Biométrico:** Sensor de pulso (MAX30102) en la cara interna del brazalete. Doble función: monitoreo de salud + autenticación biométrica para QR-Link Nivel 4 (heartbeat pattern como segundo factor).

**Expansión de pads:** Versión con 8 pads para chording completo sin necesidad de combinaciones de 3+ pads. Más rápido para texto pero más complejo de aprender.

---

## 10. Referencias

### Productos de referencia
- **TapXR / TapStrap 2** — Wearable chording keyboard comercial ($149-199)
- **Meta sEMG Wristband** — EMG-based input de Reality Labs (prototipo)
- **Clawtype** — Chorded keyboard DIY open source (Rust, RP2040)
- **ComputeDeck-B3** — Wrist-mounted cyberdeck con chording keyboard
- **Engelbart Keyset** — El chorded keyboard original (1968)

### Hardware
- ESP32-S3 Capacitive Touch Documentation (Espressif)
- ESP32 Touch Sensor Application Note
- TinyWatch S3 — Open source ESP32-S3 smartwatch (referencia de form factor)

### Librerías
- Arduino BLE library (ESP32)
- NimBLE (BLE stack eficiente para ESP32)
- ESP32 Touch Pad driver (ESP-IDF)
- PlatformIO (build system para firmware)
