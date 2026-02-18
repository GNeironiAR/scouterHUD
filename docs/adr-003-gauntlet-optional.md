# ADR-003: ScouterGauntlet como accesorio opcional

**Estado:** Aceptada
**Fecha:** Febrero 2026
**Autor:** Ger
**Afecta a:** ScouterGauntlet, ScouterApp, prioridades de desarrollo, BOM, compras

---

## Contexto

El ScouterGauntlet es un brazalete de antebrazo basado en ESP32-S3 con 5 pads capacitivos, motor de vibración, y comunicación BLE. Fue diseñado como el input silencioso del ScouterHUD — la alternativa a la voz para navegar menús, ingresar PINs, y controlar el HUD sin hablar.

Con la adopción de la ScouterApp como input principal (ver [ADR-002](adr-002-app-primary-input.md)), el Gauntlet cubre un subset de casos de uso que la app no puede resolver:

| Caso de uso | ScouterApp | Gauntlet |
|---|:---:|:---:|
| Uso diario normal | **Sí** | Sí |
| Guantes médicos (nitrilo fino) | **Sí** (con tactile overlay) | Sí |
| Guantes industriales gruesos | No | **Necesario** |
| Ambiente mojado / IP67 | Depende del case | **Mejor** |
| Sin celular disponible | No | **Necesario** |
| Manos muy sucias | Riesgoso | **Mejor** |

Estos son edge cases legítimos pero no cubren al 90%+ de los usuarios potenciales.

---

## Decisión

**El ScouterGauntlet se mantiene en el ecosistema pero pasa de componente prioritario a accesorio opcional.** Se posterga su desarrollo hasta después del MVP del HUD y la app.

Implicancias inmediatas:

1. **No se construye ahora:** Los componentes específicos del Gauntlet (ESP32 Waveshare individual, motores de vibración, LiPo 400mAh) se eliminan de la compra inicial
2. **El diseño se conserva:** El documento técnico ([gauntlet-tech-doc.md](gauntlet-tech-doc.md)) se mantiene actualizado
3. **La arquitectura lo soporta:** El `InputManager` del HUD acepta cualquier `InputBackend` por BLE GATT — la app y el Gauntlet usan el mismo protocolo, el HUD no distingue la fuente
4. **Los ESP32 del Bridge sirven para prototipar:** Si se quiere validar el concepto del Gauntlet, los ESP32-S3 SuperMini comprados para el Bridge son compatibles

---

## Razones

### La app cubre el 90% de los casos

Con la ScouterApp + tactile overlay opcional, la mayoría de las interacciones están resueltas:

- Navegación D-pad
- QR scanning (cámara del celular)
- Autenticación biométrica (FaceID/huella)
- Entrada de PIN/TOTP (numpad en pantalla)
- Device list y configuración

Solo los escenarios extremos (guantes gruesos, IP67, sin celular) requieren el Gauntlet.

### Priorización de desarrollo

El tiempo y recursos son limitados. La prioridad es:

1. **HUD funcional** — Hardware óptico + software de rendering + conectividad MQTT
2. **ScouterApp PoC** — WebSocket + HTML para validar input remoto
3. **ScouterBridge demos** — ESP32 + CAN bus para demostrar dispositivos reales
4. **Gauntlet** — Cuando los 3 anteriores estén validados

Construir el Gauntlet ahora significaría firmware ESP32 custom (C++/Arduino), diseño de PCB, impresión 3D, y testing de touch capacitivo — todo antes de tener un HUD funcional con el que testearlo.

### Ahorro de costos en compra inicial

Componentes eliminados de la compra inmediata:

| Componente | Precio |
|---|---|
| Waveshare ESP32-S3-Zero (individual, con header) | ~$7 |
| Waveshare ESP32-S3-Zero (individual, sin header) | ~$6 |
| Motores vibración coin 10mm (pack x15) | ~$7 |
| LiPo 400mAh 502035 | ~$8 |
| LiPo 400mAh 802030 (alternativa) | ~$8 |
| **Ahorro estimado** | **~$28-36** |

Nota: El pack de ESP32-S3 SuperMini (x3-4) se mantiene porque se usa para el Bridge y sirve como spare para prototipar.

---

## Implicancias

### Positivas

1. **Menor costo inicial:** ~$28-36 menos en la primera compra
2. **Desarrollo más enfocado:** Recursos concentrados en HUD + App + Bridge
3. **Validación del concepto sin hardware custom:** La app valida que el input remoto funciona antes de invertir en hardware dedicado
4. **Sin pérdida de funcionalidad:** El 90%+ de los usuarios no necesitan el Gauntlet

### Negativas / Trade-offs

1. **Sin opción para guantes gruesos inicialmente:** Los usuarios industriales con guantes gruesos no tienen input silencioso hasta que se construya el Gauntlet
2. **Sin opción sin celular inicialmente:** Usuarios sin celular o en entornos donde el celular está prohibido no tienen input alternativo
3. **Delay en el feedback del mercado:** No sabremos cuánta demanda real tiene el Gauntlet hasta que se construya

### Mitigaciones

- **CLI para desarrollo:** `--demo` y flags CLI permiten operar el HUD sin app ni Gauntlet
- **ESP32 SuperMini como prototipo:** Si surge necesidad urgente, los ESP32 del Bridge pueden usarse para un prototipo rápido del Gauntlet
- **Arquitectura lista:** El `InputManager`, `InputBackend`, y el protocolo BLE GATT ya están diseñados para soportar el Gauntlet sin cambios en el HUD
- **El Gauntlet sigue documentado:** El diseño técnico completo existe en [gauntlet-tech-doc.md](gauntlet-tech-doc.md)

---

## Alternativas consideradas

### 1. Construir el Gauntlet como prioridad junto al HUD (RECHAZADA)

- Pros: Ecosistema completo desde el día 1
- Contras: Duplica el esfuerzo de hardware, firmware ESP32 custom antes de tener HUD funcional, costo adicional innecesario
- Razón: Mejor validar el concepto de input remoto con la app (rápido, barato) antes de invertir en hardware custom

### 2. Eliminar el Gauntlet del ecosistema (RECHAZADA)

- Pros: Simplifica la documentación y el scope
- Contras: Pierde los edge cases legítimos (guantes gruesos, IP67, sin celular). Algunos usuarios necesitan input sin celular
- Razón: El Gauntlet tiene valor real para ciertos usuarios. Eliminarlo sería cerrar puertas innecesariamente

### 3. Comprar todos los componentes del Gauntlet ahora "por si acaso" (RECHAZADA)

- Pros: Los componentes están disponibles cuando se necesiten
- Contras: ~$28-36 en componentes que podrían no usarse por meses. Algunos componentes (LiPo) tienen shelf life
- Razón: Los componentes son baratos y fácilmente disponibles en Amazon. Mejor comprar cuando se necesiten

### 4. Usar un producto comercial (TapXR, TapStrap) en vez de construir (RECHAZADA)

- Pros: Hardware ya validado y funcional
- Contras: $149-199 vs $12-20, no es open source, no se integra directamente con el protocolo custom BLE GATT
- Razón: Contrario a la filosofía del proyecto (open source, bajo costo). El Gauntlet custom es 10x más barato

---

## Cuándo reconsiderar

El Gauntlet debe volver a ser prioridad cuando:

1. El HUD base esté funcional (óptica validada, rendering estable)
2. La ScouterApp PoC esté funcionando (WebSocket + D-pad)
3. Se identifique demanda concreta de usuarios que necesitan input sin celular
4. Se tenga tiempo/recursos libres de los componentes prioritarios

**Estimado:** Phase G0 (PoC con breadboard) podría iniciarse después de Phase A0 (App PoC) — probablemente 4-6 semanas desde ahora.

---

## Documentos relacionados

- [gauntlet-tech-doc.md](gauntlet-tech-doc.md) — Diseño técnico completo del Gauntlet
- [ADR-002: ScouterApp como input principal](adr-002-app-primary-input.md) — La decisión que hace al Gauntlet opcional
- [ADR-001: Cámara opcional](adr-001-camera-optional.md) — Decisión relacionada sobre privacidad
- [app-tech-doc.md](app-tech-doc.md) — Diseño de la app que reemplaza al Gauntlet como input principal
- [TECH_DESIGN.md](TECH_DESIGN.md) — Diseño técnico general (v0.3+)
