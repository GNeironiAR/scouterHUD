# ADR-002: ScouterApp como input principal del ecosistema

**Estado:** Aceptada
**Fecha:** Febrero 2026
**Autor:** Ger
**Afecta a:** ScouterHUD, ScouterApp, ScouterGauntlet, arquitectura de input, autenticación

---

## Contexto

El diseño original del ScouterHUD contemplaba tres fuentes de input:

1. **Voz** — STT para comandos y dictado
2. **Cámara del HUD** — Escaneo de QR codes para descubrir dispositivos
3. **ScouterGauntlet** — Brazalete ESP32 con pads capacitivos para input silencioso

Al decidir remover la cámara del HUD (ver [ADR-001](adr-001-camera-optional.md)), se necesitaba un mecanismo de reemplazo para el escaneo de QR codes. Simultáneamente, el Gauntlet representaba un costo y complejidad adicional ($15-20 + firmware ESP32 + hardware custom) para resolver un problema que la mayoría de los usuarios ya tiene resuelto: **su celular**.

La pregunta era: ¿construimos hardware custom (Gauntlet) como input principal, o aprovechamos el dispositivo que el usuario ya tiene en el bolsillo?

---

## Decisión

**La ScouterApp (aplicación de celular) se convierte en el input principal del ecosistema ScouterHUD.** Asume tres funciones críticas:

1. **Escáner QR** — Reemplaza la cámara del HUD para descubrir dispositivos
2. **Autenticación biométrica** — FaceID/huella reemplaza PIN/TOTP manual
3. **Control remoto** — D-pad, numpad, device list, configuración del HUD

El celular se monta en el antebrazo del usuario (landscape) con un strap, proporcionando acceso rápido sin soltar lo que tenga en las manos.

---

## Razones

### El celular ya tiene todo

| Capacidad | Hardware dedicado | Celular del usuario |
|---|---|---|
| Cámara para QR | Pi Camera ~$12 | Incluida (mejor calidad) |
| Biometría | No disponible en HUD | FaceID / huella nativa |
| Display para UI | No (HUD es monocular, limitado) | Pantalla táctil full-color |
| Conectividad BLE/WiFi | — | Incluida |
| Procesamiento | — | Más potente que Pi Zero |
| **Costo adicional** | **$12-30** | **$0** |

### Autenticación biométrica (ventaja decisiva)

Con la ScouterApp, la autenticación deja de ser un problema:

| Antes (sin app) | Con ScouterApp |
|---|---|
| PIN 4 dígitos manual en HUD (lento, visible) | Huella dactilar 0.3s (rápido, silencioso) |
| TOTP 6 dígitos con timer (tedioso) | FaceID 0.5s (automático) |
| Decir código en voz alta (inseguro) | Silencioso, no observable |
| Credenciales en texto plano o memoria | Hardware seguro (Keychain/Keystore) |

Las credenciales se almacenan en el **hardware seguro del celular** (Secure Enclave en iOS, StrongBox en Android), protegidas por biometría. Esto es más seguro que cualquier método de input manual.

### Cero costo adicional

La ScouterApp es software gratuito. El usuario ya tiene el celular. El strap de antebrazo cuesta ~$5 o se imprime en 3D. No hay BOM adicional.

### Desarrollo más rápido

- **PoC inmediato:** Una página HTML + WebSocket valida el concepto en horas, sin hardware
- **Flutter MVP:** Un codebase para Android + iOS, sin firmware custom
- **Sin hardware custom:** No hay PCBs que diseñar, fabricar, y ensamblar

---

## Implicancias

### Positivas

1. **$0 de costo adicional** para el input principal del ecosistema
2. **Autenticación biométrica nativa** — seguridad superior a PIN/TOTP manual
3. **QR scanning con cámara superior** — la cámara del celular es mejor que cualquier Pi Camera
4. **Desarrollo rápido** — PoC WebSocket sin hardware, Flutter MVP multiplataforma
5. **Menor barrera de entrada** — el usuario no necesita construir/comprar hardware adicional
6. **UI rica** — pantalla táctil full-color para configuración, device list, etc.

### Negativas / Trade-offs

1. **Dependencia del celular:** Sin celular, no hay input principal (mitigation: Gauntlet opcional, CLI para desarrollo)
2. **No impermeable:** El celular no es IP67 en la mayoría de los casos (mitigation: case resistente al agua)
3. **Guantes gruesos:** Los guantes industriales gruesos no funcionan con pantallas táctiles (mitigation: Gauntlet ESP32 para este caso, o tactile overlay con material conductivo)
4. **Batería del celular:** Uso continuo de la app drena batería del celular más rápido
5. **Un dispositivo más que cargar:** Aunque el celular ya se carga diariamente

### Niveles de seguridad actualizados

| Nivel | Método | Ejemplo |
|---|---|---|
| 0 — Open | Sin auth | Termostato, datos públicos |
| 1 — Biometric | FaceID/huella desbloquea credencial almacenada | Monitor médico, vehículo personal |
| 2 — Biometric + PIN | Biometría + PIN cada N minutos | Servidor producción |
| 3 — Mutual TLS | Certificados mutuos | Infraestructura crítica |
| 4 — Multi-factor | Biometría + certificado + aprobación remota | Militar, nuclear |

---

## Alternativas consideradas

### 1. Gauntlet ESP32 como input principal (RECHAZADA para input principal, MANTENIDA como opcional)

- Pros: Hardware dedicado, funciona sin celular, IP67, funciona con guantes gruesos
- Contras: Costo adicional $15-20, requiere firmware custom, sin biometría, sin cámara para QR
- Razón: Para el 90%+ de los usuarios, el celular es superior en todo. El Gauntlet cubre edge cases legítimos pero no justifica ser el input principal

### 2. Voice-only (sin app ni Gauntlet) (RECHAZADA)

- Pros: Máxima simplicidad, hands-free total
- Contras: No funciona en ambientes silenciosos ni ruidosos, PINs inseguros por voz, sin QR scanning
- Razón: La voz es un complemento, no puede ser el único input

### 3. App + Gauntlet como co-principales (RECHAZADA)

- Pros: Máxima flexibilidad
- Contras: Complica la documentación, el onboarding, y las instrucciones. El usuario no sabe cuál comprar/usar primero
- Razón: Un input principal claro (app) con un accesorio opcional (Gauntlet) es más simple de comunicar

### 4. Smart ring como input (RECHAZADA)

- Pros: Ultra discreto, siempre puesto
- Contras: Hardware custom complejo, sin estándar abierto, sin capacidad de QR scanning ni biometría
- Razón: Demasiado complejo para el estado actual del proyecto

---

## Plan de implementación

### Phase A0 — PoC WebSocket (se puede hacer ahora, sin hardware)
- WebSocket server en el HUD
- `PhoneInput` backend que recibe eventos por WebSocket
- HTML page con D-pad + numpad (se abre desde el browser del celular)

### Phase A1 — Flutter MVP
- Flutter app con QR scanning + biometría + D-pad
- Comunicación BLE con el HUD
- Landscape mode con strap mount

### Phase A2 — Tactile Overlay
- Membrana de silicona/TPU con relieves para operar sin mirar
- Compatible con guantes médicos (nitrilo)

---

## Documentos relacionados

- [app-tech-doc.md](app-tech-doc.md) — Diseño técnico completo de la ScouterApp
- [ADR-001: Cámara opcional](adr-001-camera-optional.md) — La decisión que motivó la necesidad de la app
- [ADR-003: Gauntlet opcional](adr-003-gauntlet-optional.md) — El Gauntlet como accesorio, no como principal
- [camera-tech-doc.md](camera-tech-doc.md) — Módulo de cámara opcional
- [TECH_DESIGN.md](TECH_DESIGN.md) — Diseño técnico general (v0.3+)
