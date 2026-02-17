# ScouterApp — Companion App for ScouterHUD

## Technical Design Document v0.1

**Project Codename:** ScouterApp
**Companion to:** ScouterHUD
**Author:** Ger
**Date:** February 2026
**License:** MIT
**Status:** Diseño

---

## 1. Vision & Scope

### 1.1 El problema

ScouterHUD necesita un método de input silencioso, rápido y accesible. La voz no sirve en ambientes silenciosos, ruidosos o privados. Construir un hardware custom (ESP32 + pads) agrega costo, complejidad y tiempo — cuando la mayoría de los usuarios ya tienen un dispositivo perfecto en el bolsillo: su celular.

### 1.2 Qué es ScouterApp

Una aplicación para Android/iOS que se monta en el antebrazo con un strap y funciona como el control principal del ScouterHUD. Se comunica por BLE o WiFi con el HUD y ofrece:

- D-pad para navegación
- Teclado numérico para PIN/TOTP
- Lista de dispositivos conectados
- Quick actions (scan QR, toggle voice, lock)
- Configuración del HUD

**Orientación: Landscape** — el celular se monta horizontal en el antebrazo, porque cuando mirás tu brazo, el antebrazo está perpendicular a tu línea de visión.

### 1.3 Qué NO es

- No reemplaza el HUD (no muestra los datos AR)
- No es obligatoria (el HUD funciona con voz y QR sin la app)
- No es un segundo display — es un control remoto inteligente

### 1.4 Accesorio opcional: Tactile Overlay

Una membrana de silicona/TPU impresa 3D que se coloca sobre la pantalla del celular:

- **Relieves táctiles** que permiten ubicar los "botones" sin mirar
- **Fina** (~0.5mm) para transmitir toque capacitivo
- **Compatible con guantes médicos** (nitrilo/látex son conductivos)
- Los botones de la app se alinean con los relieves de la membrana

Esto resuelve el caso de uso del Gauntlet ESP32 (operación a ciegas, con guantes) sin hardware adicional.

```
┌────────────────────────────────────────────┐
│             MEMBRANA (vista superior)        │
│                                             │
│  ╔══════╗ ╔══════╗ ╔══════╗ ╔══════╗       │
│  ║ ◄    ║ ║  ▲   ║ ║  ▼   ║ ║  ►   ║       │  ← relieves en
│  ╚══════╝ ╚══════╝ ╚══════╝ ╚══════╝       │     silicona/TPU
│                                             │
│                 ╔══════════╗                 │
│                 ║ CONFIRM  ║                 │
│                 ╚══════════╝                 │
│─────────────────────────────────────────────│  ← membrana ~0.5mm
│  ┌─────────────────────────────────────┐    │
│  │       PANTALLA TÁCTIL (celular)     │    │  ← touch screen debajo
│  └─────────────────────────────────────┘    │
└────────────────────────────────────────────┘
```

---

## 2. Pantallas de la app (landscape)

### 2.1 Pantalla principal — Control

```
┌──────────────────────────────────────────────────┐
│ ScouterApp                     🔋 HUD: 78%  🟢   │
│──────────────────────────────────────────────────│
│                                                   │
│   ┌──────┐                          ┌──────────┐ │
│   │  ▲   │                          │          │ │
│   │      │                          │  CONFIRM │ │
│   │◄    ►│                          │          │ │
│   │      │                          └──────────┘ │
│   │  ▼   │                                       │
│   └──────┘                          ┌──────────┐ │
│                                     │  CANCEL  │ │
│                                     └──────────┘ │
│──────────────────────────────────────────────────│
│  [Devices]  [Scan QR]  [PIN Pad]  [Settings]    │
└──────────────────────────────────────────────────┘
```

Botones grandes, espaciados, operables con el pulgar de la mano contraria.

### 2.2 Pantalla PIN — Teclado numérico

```
┌──────────────────────────────────────────────────┐
│ PIN for: monitor-bed-12              [Cancel]     │
│──────────────────────────────────────────────────│
│                                                   │
│      ┌─────┐  ┌─────┐  ┌─────┐                  │
│      │  1  │  │  2  │  │  3  │                  │
│      ├─────┤  ├─────┤  ├─────┤                  │
│      │  4  │  │  5  │  │  6  │                  │
│      ├─────┤  ├─────┤  ├─────┤                  │
│      │  7  │  │  8  │  │  9  │     [  ⌫  ]      │
│      ├─────┤  ├─────┤  ├─────┤                  │
│      │     │  │  0  │  │     │     [SUBMIT]      │
│      └─────┘  └─────┘  └─────┘                  │
│                                                   │
└──────────────────────────────────────────────────┘
```

### 2.3 Pantalla dispositivos

```
┌──────────────────────────────────────────────────┐
│ Connected Devices (3)                 [Back]      │
│──────────────────────────────────────────────────│
│                                                   │
│  ● monitor-bed-12      medical    [PIN] [ACTIVE] │
│    car-001              vehicle          [CONNECT]│
│    press-machine-07     industrial [PIN] [CONNECT]│
│                                                   │
│──────────────────────────────────────────────────│
│  [Scan New QR]                   [Disconnect All] │
└──────────────────────────────────────────────────┘
```

### 2.4 Settings

- Conexión WiFi/BLE con el HUD
- Brillo del HUD
- Layout preferences
- Overlay calibration (alinear botones con la membrana)

---

## 3. Comunicación App ↔ HUD

### 3.1 Protocolo

La app usa **exactamente el mismo protocolo BLE GATT** que el Gauntlet ESP32:

```
BLE Service UUID:        a0e9f5b0-5c1a-4d3e-8f2a-1b3c5d7e9f01

Characteristics:
├── input_event (notify → HUD)     Botón presionado en la app
├── mode_status (read/write)       Modo actual (nav/num/text)
├── haptic_command (write → App)   HUD pide vibración al celular
└── hud_status (read/notify)       Estado del HUD (batería, device activo)
```

Esto significa que:
- El `InputManager` del HUD no distingue si el evento viene de la app o del Gauntlet
- Ambos son un `InputBackend` que produce `InputEvent`
- El mismo `gauntlet_input.py` (renombrado a `ble_input.py`) sirve para ambos

### 3.2 Alternativa WiFi

Para latencia más baja o cuando BLE no está disponible, la app puede comunicarse por WebSocket sobre WiFi local:

```
App ──WebSocket──► HUD (ws://scouterhud.local:8765)
```

Mismo formato de mensajes, diferente transporte. El `InputManager` del HUD maneja ambos.

### 3.3 Modo relay MQTT

La app puede actuar como relay: el celular se conecta al broker MQTT y retransmite datos al HUD. Útil cuando el HUD no tiene WiFi directo pero sí BLE al celular.

---

## 4. Tactile Overlay — Diseño

### 4.1 Materiales

| Material | Conductivo? | Con guantes nitrilo? | Con guantes gruesos? |
|----------|:-----------:|:--------------------:|:--------------------:|
| Silicona fina (0.3-0.5mm) | Sí (capacitivo pasa) | Sí | No |
| TPU impreso 3D (0.4mm) | Sí | Sí | No |
| Membrana conductiva (silver mesh) | Sí | Sí | Sí |
| Film PET con adhesivo conductivo | Sí | Sí | Parcial |

**MVP:** Silicona fina con relieves moldeados. Se puede fabricar con molde impreso 3D + silicona de casteo.

**Pro:** Membrana conductiva tipo "touchscreen glove" material, cortada a medida.

### 4.2 Relieves táctiles

```
Vista de perfil del overlay:

     ┌─┐   ┌─┐   ┌─┐   ┌─┐         ← ridges (1mm alto)
─────┘ └───┘ └───┘ └───┘ └─────────  ← membrana base (0.5mm)
═══════════════════════════════════   ← pantalla del celular
```

- **Ridges** de 1mm entre zonas de botón → se sienten con el dedo
- **Dot** en relieve en el botón CONFIRM → orientación sin mirar
- **Bordes elevados** en el D-pad → los 4 direcciones se distinguen por tacto

### 4.3 Tamaños estándar

Se diseñan overlays para los tamaños de celular más comunes:
- Small: 5.5-6.0" (ej: iPhone SE, Pixel 7a)
- Medium: 6.1-6.4" (ej: iPhone 15, Galaxy S24)
- Large: 6.5-6.8" (ej: iPhone 15 Plus, Galaxy S24 Ultra)

La app tiene un modo de calibración que muestra los botones y el usuario ajusta la posición del overlay.

---

## 5. Stack técnico

### 5.1 Opciones de desarrollo

| Framework | Plataforma | BLE | Pros | Contras |
|-----------|-----------|-----|------|---------|
| **Flutter** | Android + iOS | flutter_blue_plus | Un codebase, UI nativa, rápido | Dart no es Python |
| **React Native** | Android + iOS | react-native-ble-plx | JS ecosystem, familiar | BLE a veces problemático |
| **Kotlin/Swift nativo** | Separado | Nativo | Máximo control BLE | Doble codebase |
| **PWA + Web Bluetooth** | Chrome Android | Web Bluetooth API | Sin instalar, solo web | Solo Chrome, no iOS |

**Recomendación:** Flutter para MVP. BLE bien soportado, un solo codebase, buen rendimiento de UI.

**Alternativa rápida para PoC:** PWA con Web Bluetooth — cero instalación, se prueba desde el browser. Limitado a Android/Chrome pero valida el concepto en minutos.

### 5.2 Comunicación

```
ScouterApp (celular)
  │
  ├── BLE GATT ──► ScouterHUD (Pi Zero)
  │                  └── InputManager.poll()
  │
  ├── WiFi/WebSocket ──► ScouterHUD
  │
  └── MQTT (relay mode) ──► Broker ──► ScouterHUD
```

---

## 6. Roadmap

### Phase A0 — PoC WebSocket (se puede hacer AHORA, sin hardware)

- [ ] WebSocket server en el HUD (`ws://localhost:8765`)
- [ ] `PhoneInput` backend que recibe eventos por WebSocket
- [ ] HTML page simple con D-pad + numpad (se abre desde el browser del celular)
- [ ] Integrar `PhoneInput` al `InputManager` existente
- [ ] Testear con emulador + preview mode

**Criterio de éxito:** Abrir una página web en el celular → tocar botón → HUD responde.

### Phase A1 — App Flutter MVP

- [ ] Flutter app con pantalla de control (D-pad + confirm + cancel)
- [ ] Pantalla de PIN entry (numpad)
- [ ] Pantalla de device list
- [ ] Comunicación BLE con el HUD
- [ ] Pairing flow (escanear QR del HUD)
- [ ] Landscape mode forzado

### Phase A2 — Tactile Overlay

- [ ] Diseño 3D del overlay para 2-3 tamaños de celular
- [ ] Prototipo con silicona de casteo + molde 3D
- [ ] Modo calibración en la app
- [ ] Validar con guantes de nitrilo

### Phase A3 — Features avanzados

- [ ] Modo relay MQTT (celular como puente WiFi→BLE)
- [ ] Notificaciones push de alertas del HUD
- [ ] QR scan desde cámara del celular (además de la del HUD)
- [ ] Configuración remota del HUD (brillo, layouts)
- [ ] Widget de Android para quick status

---

## 7. Relación con ScouterGauntlet (ESP32)

El Gauntlet ESP32 **no desaparece** — pasa a ser un accesorio opcional para casos extremos:

| Caso | ScouterApp | Gauntlet ESP32 |
|------|:---------:|:--------------:|
| Uso diario | **Principal** | — |
| Guantes médicos (nitrilo) | **Sí** (con overlay) | Sí |
| Guantes gruesos (industrial) | No | **Necesario** |
| Ambiente mojado/IP67 | Depende del case | **Mejor** |
| Sin celular | — | **Necesario** |
| Manos extremadamente sucias | Riesgoso | **Mejor** |
| Máximo cyberpunk | Opcional | **Sí** |

Ambos usan el mismo protocolo BLE GATT, el mismo `InputBackend`, los mismos `InputEvent`. El HUD no distingue la fuente.

---

## 8. Repositorio

```
scouterhud/
├── ...todo lo del HUD...
├── app/
│   ├── web/                  → PoC WebSocket (HTML + JS)
│   ├── flutter/              → App Flutter (Android + iOS)
│   └── overlay/
│       ├── 3d-models/        → STL del tactile overlay
│       └── calibration/      → Guía de alineación
├── gauntlet/                 → (opcional) ESP32 firmware
└── bridge/                   → ESP32 firmware
```

---

*ScouterApp es parte del ecosistema ScouterHUD. Open source bajo licencia MIT.*
