# ScouterHUD Camera Module — Optional Add-on

## Technical Design Document v0.1

**Project Codename:** ScouterCam
**Companion to:** ScouterHUD
**Author:** Ger
**Date:** February 2026
**License:** MIT (Software) / CERN-OHL-S v2 (Hardware)
**Status:** Opcional — no incluida en el HUD base

---

## 1. Por qué la cámara es opcional

### 1.1 Privacidad: la razón principal

**La cámara fue removida del ScouterHUD base por una decisión deliberada de privacidad.**

Un dispositivo wearable con cámara siempre encendida genera problemas serios:

- **Grabación no consentida:** Las personas alrededor no saben si están siendo grabadas. Esto es especialmente problemático en hospitales, oficinas, reuniones y espacios privados.
- **Percepción social:** Un dispositivo con cámara visible genera rechazo y desconfianza inmediata — el efecto "Glassholes" que destruyó Google Glass socialmente.
- **Regulaciones:** HIPAA (salud), GDPR (Europa), y legislación local en muchos países prohíben o restringen la grabación en ciertos espacios. Un wearable con cámara entra en zona gris legal.
- **Prohibiciones físicas:** Muchos hospitales, juzgados, laboratorios, datacenters y fábricas prohíben explícitamente dispositivos con cámara. Si el HUD tiene cámara, **no puede entrar**.
- **Confianza del usuario:** El usuario quiere un HUD que le muestre datos, no un dispositivo que otros perciban como una cámara espía.

### 1.2 La solución: el celular escanea

Con la ScouterApp, el **celular del usuario escanea los QR codes** usando su propia cámara:

```
Sin cámara en el HUD:                  Con cámara en el HUD (opcional):

El usuario ve un QR                    El usuario mira un QR
en un dispositivo                      a través del HUD
      │                                       │
      ▼                                       ▼
Levanta el brazo y                     La cámara del HUD
escanea con la app ─────┐             detecta el QR ─────┐
del celular              │                                 │
      │                  │                                 │
      ▼                  │                                 │
La app envía la URL      │             El HUD procesa      │
al HUD por BLE/WiFi ────┘             directamente ───────┘
      │                                       │
      ▼                                       ▼
El HUD se conecta                      El HUD se conecta
y muestra los datos                    y muestra los datos
```

**El resultado es el mismo.** La diferencia es que sin cámara:
- El HUD es un **dispositivo puro de display** — más simple, más barato, más aceptable socialmente
- El escaneo es **intencional** — el usuario activamente apunta el celular, no hay ambigüedad sobre qué se está escaneando
- La cámara del celular **ya existe** y es mejor que cualquier Pi Camera ($0 de costo adicional)
- El HUD puede **entrar a cualquier espacio** sin restricciones

### 1.3 Cuándo SÍ tiene sentido la cámara

La cámara como módulo opcional se justifica en estos escenarios específicos:

| Escenario | Por qué la cámara ayuda |
|-----------|------------------------|
| **Escaneo continuo** | Técnico recorriendo decenas de dispositivos — levantar el celular cada vez es lento |
| **Manos completamente ocupadas** | Cirujano, soldador, operador de maquinaria pesada |
| **Sin celular** | Entornos donde el celular está prohibido pero la cámara del HUD está autorizada |
| **AR avanzado** | Futuras features: reconocimiento de objetos, OCR, SLAM tracking |
| **Accesibilidad** | Usuarios con movilidad reducida que no pueden levantar el brazo |

**Importante:** Estos son edge cases. Para el 90%+ de los usuarios, escanear con el celular es suficiente y preferible.

---

## 2. Hardware del módulo de cámara

### 2.1 Componentes

| # | Componente | Modelo recomendado | Precio aprox. |
|---|-----------|-------------------|---------------|
| 1 | Cámara | Pi Camera Module v2 (o compatible Zero) | ~$10-15 |
| 2 | Cable flex | FPC 15-pin, longitud según housing | ~$2 |
| 3 | Indicador LED | LED rojo/verde para indicar cuando la cámara está activa | ~$0.10 |

**Costo adicional: ~$12-17 USD**

### 2.2 Indicador obligatorio de actividad

**Si se usa el módulo de cámara, DEBE tener un LED indicador visible que no se pueda desactivar por software:**

```
┌──────────────────────────────┐
│  SCOUTERHUD (vista frontal)  │
│                              │
│    ┌──────┐  🔴 ← LED       │
│    │CAMERA│  (siempre encendido │
│    │MODULE│   cuando la cámara  │
│    └──────┘   está activa)      │
│                              │
│    ┌────────────┐            │
│    │  DISPLAY   │            │
│    │  ST7789    │            │
│    └────────────┘            │
└──────────────────────────────┘
```

- **LED rojo fijo:** Cámara activa (escaneando)
- **LED apagado:** Cámara inactiva (off por hardware, no solo software)
- **No bypasseable:** El LED está conectado directamente a la alimentación de la cámara, no controlado por GPIO. Si la cámara recibe corriente, el LED se enciende. Sin excepciones.

Esto es una decisión de diseño ética: cualquier persona cerca del usuario puede ver si la cámara está activa.

### 2.3 Modos de operación de la cámara

| Modo | Comportamiento | LED | Privacidad |
|------|---------------|-----|------------|
| **Off (default)** | Cámara sin alimentación, módulo deshabilitado | Apagado | Máxima |
| **Scan-on-demand** | Se activa solo al presionar botón de scan, se apaga al detectar QR | Parpadea | Alta |
| **Scan continuous** | Activa durante la sesión, escanea QR continuamente | Encendido fijo | Media |

**Default:** Off. La cámara solo se activa por acción explícita del usuario.

---

## 3. Software

### 3.1 Integración con el HUD

El módulo de cámara se integra como un backend opcional del sistema existente:

```
software/scouterhud/camera/
├── backend.py              → ABC CameraBackend (ya existe)
├── backend_desktop.py      → Webcam/archivo para desarrollo (ya existe)
└── backend_pi.py           → PiCamera backend (módulo opcional)
```

`backend_pi.py` implementa `CameraBackend`:

```python
class PiCameraBackend(CameraBackend):
    """Optional Pi Camera module for on-HUD QR scanning.

    Only available when the camera hardware module is installed.
    Falls back gracefully if picamera2 is not available.
    """

    def __init__(self):
        try:
            from picamera2 import Picamera2
            self._camera = Picamera2()
            self._available = True
        except ImportError:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def capture_frame(self) -> bytes | None:
        """Capture a single frame for QR scanning."""
        ...

    def start_continuous(self):
        """Start continuous scanning mode."""
        ...

    def stop(self):
        """Stop camera and cut power (LED goes off)."""
        ...
```

### 3.2 QR scanning desde la app (modo principal)

Cuando la cámara no está presente (configuración por defecto), el escaneo de QR funciona así:

```
ScouterApp (celular)                    ScouterHUD
     │                                       │
     │  1. Usuario abre la app y             │
     │     toca "Scan QR"                    │
     │     (o gesto en Gauntlet)             │
     │                                       │
     │  2. La cámara del celular             │
     │     escanea el QR code                │
     │                                       │
     │  3. La app parsea la URL:             │
     │     qrlink://v1/{id}/mqtt/...         │
     │                                       │
     │  4. Envía la URL al HUD:              │
     │     BLE/WiFi → "qrlink://..."  ──────►│
     │                                       │
     │                                       │  5. HUD recibe URL
     │                                       │     y se conecta al
     │                                       │     dispositivo vía MQTT
     │                                       │
     │                              ◄────────│  6. Si requiere auth,
     │  7. La app pide biometría             │     HUD pide credenciales
     │     (FaceID/huella)                   │
     │                                       │
     │  8. Envía token de auth  ────────────►│
     │                                       │  9. HUD conectado,
     │                                       │     muestra datos
```

### 3.3 Prioridad de scanning

Si tanto la app como el módulo de cámara están disponibles, el sistema prioriza:

1. **App scan** — Siempre disponible, sin implicaciones de privacidad
2. **Camera scan** — Solo si está habilitado explícitamente por el usuario

El usuario puede configurar su preferencia en Settings.

---

## 4. Impacto en costos

| Configuración | Componentes HUD | Costo HUD |
|--------------|----------------|-----------|
| **HUD base (sin cámara)** | Pi Zero 2W + Display + Óptica + Batería | **~$40-45** |
| **HUD con cámara** | HUD base + Pi Camera + Cable + LED | **~$55-60** |

El ecosistema estándar sin cámara:
- HUD (~$40-45) + App ($0) + Bridge (~$8-15) = **~$48-60 USD**

---

## 5. Futuro: más allá del QR scanning

Si se incluye el módulo de cámara, abre la puerta a features avanzados post-MVP:

- **OCR en tiempo real:** Leer texto de etiquetas, pantallas, documentos
- **Reconocimiento de objetos:** Identificar equipos sin QR code (ML on-device)
- **SLAM / AR tracking:** Posicionar overlays en el espacio 3D real
- **Visual Translate:** Traducir texto en tiempo real (letreros, instrucciones)
- **Barcode scanning:** Además de QR, leer barcodes 1D estándar

Estos features requieren más potencia de cómputo que el Pi Zero 2W puede ofrecer. Una evolución futura del HUD podría usar un procesador más potente (CM4, Jetson Nano) para habilitar estos casos.

---

## 6. Decisiones de diseño

| Decisión | Elegida | Alternativa descartada | Razón |
|----------|---------|----------------------|-------|
| Cámara en HUD | **Opcional** | Incluida por defecto | Privacidad, costo, aceptación social |
| QR scanning principal | **App (celular)** | Cámara del HUD | Cero costo, mejor cámara, intencional |
| LED indicador | **Hardwired (no bypasseable)** | Controlado por GPIO | Confianza, ética, regulaciones |
| Modo default | **Off** | Scan continuous | Mínima intrusión |
| Auth con cámara | **Biometría del celular** | PIN/TOTP manual | Más seguro, más rápido, silencioso |

---

*ScouterCam es un módulo opcional del ecosistema ScouterHUD. Open source bajo licencia MIT (software) y CERN-OHL-S v2 (hardware).*
