# ScouterHUD — Un ecosistema wearable que te permite ver los datos de cualquier dispositivo con solo mirarlo

---

## La idea en una frase

**¿Y si pudieras mirar cualquier dispositivo — tu auto, un monitor médico, un servidor, un sensor — y ver sus datos flotando frente a tu ojo en tiempo real?**

ScouterHUD es un ecosistema open source que hace exactamente eso, por menos de $85 USD.

---

## Cómo funciona

El concepto es simple: cada dispositivo del mundo real tiene un pequeño código QR pegado. Cuando el usuario mira ese QR a través del ScouterHUD, el sistema se conecta automáticamente al dispositivo y muestra sus datos en vivo frente a su ojo, superpuestos sobre el mundo real. Sin tocar nada. Sin pantallas. Manos libres.

```
   Lo que ves                    Lo que pasa

   Mirás un QR en              Levantás el brazo y
   un monitor ──────────────►  escaneás el QR con
   médico                      la app del celular

   La app envía la URL         El HUD se conecta
   al HUD por BLE/WiFi ──────► al dispositivo
                               vía MQTT

   En tu ojo aparecen          Si el dispositivo
   los signos vitales ◄──────  requiere auth, la app
   del paciente                usa tu huella/FaceID
```

---

## Los componentes del ecosistema

### 1. ScouterHUD — Los ojos (~$40-45 USD)

Una vincha con una pantalla semitransparente frente al ojo derecho. Inspirado en el scouter de Vegeta de Dragon Ball Z.

**Qué hace:**
- Muestra datos superpuestos sobre tu visión real (ves el mundo + información al mismo tiempo)
- Incluye micrófono y auricular para un asistente de IA por voz
- Funciona con WiFi y Bluetooth

**Qué NO tiene (por diseño):**
- **No tiene cámara.** La decisión de no incluir cámara es deliberada: un wearable con cámara genera desconfianza, rechazo social (efecto "Glassholes"), problemas legales (HIPAA, GDPR), y prohibiciones de acceso en hospitales, juzgados y datacenters. El escaneo de QR se hace desde la app del celular — es intencional, controlado, y no levanta sospechas. Ver [camera-tech-doc.md](camera-tech-doc.md) para el módulo de cámara opcional.

**Cómo se usa:**
Se pone como una vincha. La batería en la nuca hace de contrapeso. Es cómodo por horas. Pesa menos que unos auriculares over-ear (~150g). **Sin cámara, el HUD es un dispositivo puro de display** — puede entrar a cualquier espacio sin restricciones.

---

### 2. ScouterApp — Las manos (gratis)

Una app para Android/iOS que se monta en el antebrazo con un strap. Es el control remoto principal del ScouterHUD.

**Qué hace:**
- **Escanea QR codes** con la cámara del celular y envía la URL al HUD (reemplaza la cámara del HUD, ver privacidad arriba)
- **Autenticación biométrica** (FaceID/huella) para dispositivos protegidos — reemplaza PIN/TOTP manual
- Permite controlar el HUD sin hablar (ideal para entornos silenciosos o privados)
- Navegación de menús, confirmación, cancelación con D-pad
- Gestión de dispositivos conectados, configuración del HUD
- Vibración como feedback háptico

**Cómo se usa:**
El celular se coloca horizontal (landscape) en el antebrazo con un strap. Se opera con la otra mano. La orientación landscape es natural porque el antebrazo está perpendicular a tu línea de visión cuando lo mirás.

**Accesorio opcional: Tactile Overlay** — Una membrana de silicona/TPU con relieves que se coloca sobre la pantalla del celular, permitiendo ubicar los botones sin mirar. Compatible con guantes médicos (nitrilo). Se imprime en 3D el molde y se castea en silicona.

**¿Por qué no solo voz?** Porque no podés decir un código TOTP en voz alta en una oficina, ni darle instrucciones a un asistente de IA en una sala de hospital silenciosa, ni hablarle a tu dispositivo en un ambiente industrial ruidoso.

---

### 3. ScouterGauntlet — Accesorio pro (opcional, ~$15 USD)

Un brazalete con 5 pads táctiles capacitivos, basado en ESP32. Inspirado en la computadora de muñeca del Predator.

**Para quién:** Usuarios que necesitan operación con guantes gruesos (industrial, soldadura), ambientes mojados/IP67, o máxima discreción sin celular.

**Nota:** Para el 90% de los usuarios, la ScouterApp es suficiente. El Gauntlet es para casos extremos.

---

### 4. ScouterBridge — El traductor (~$8-15 USD)

Un pequeño dongle que se conecta a cualquier dispositivo existente y lo hace compatible con el ecosistema.

**Qué hace:**
- Se enchufa a un dispositivo que no fue diseñado para este sistema (un auto, un monitor médico, un sensor industrial, un servidor)
- Lee los datos del dispositivo en su idioma nativo (USB, serial, OBD-II, Bluetooth)
- Los traduce y los publica en el formato que el ScouterHUD entiende
- Incluye un QR code que el usuario escanea para conectarse

**Por qué es necesario:**
Ningún dispositivo del mundo habla nuestro protocolo QR-Link todavía — es nuevo. El Bridge resuelve ese problema: lleva QR-Link a cualquier dispositivo que ya existe, sin modificarlo.

**Viene en 4 sabores:**
- **USB Bridge** — Para dispositivos con puerto USB (monitores, impresoras, instrumentos)
- **OBD-II Bridge** — Para autos (se enchufa al puerto de diagnóstico)
- **Serial Bridge** — Para sensores industriales y PLCs
- **BLE Bridge** — Para dispositivos Bluetooth (oxímetros, bandas fitness, sensores)

---

## El protocolo que une todo: QR-Link

QR-Link es un protocolo abierto que inventamos para este proyecto. Define cómo cualquier dispositivo anuncia su identidad y sus datos a través de un simple código QR.

**Así funciona:**

1. Un dispositivo (o su Bridge) tiene un QR pegado
2. El QR contiene: quién soy, dónde están mis datos, cómo conectarse
3. El ScouterHUD escanea el QR con su cámara
4. Se conecta automáticamente al dispositivo
5. Recibe datos en vivo y los muestra en la pantalla

**Es como Bluetooth pairing, pero visual.** En vez de buscar dispositivos en un menú, simplemente mirás el QR y ya estás conectado.

**Seguridad:** Los datos sensibles (médicos, financieros) están protegidos. El QR te dice que el dispositivo existe, pero para ver sus datos necesitás autenticarte — con la **biometría del celular** (FaceID/huella), que desbloquea las credenciales almacenadas de forma segura (Keychain/Keystore). Para niveles más altos: certificados digitales o aprobación remota. Toda la comunicación es **local y encriptada** — no pasa por la nube.

---

## Casos de uso reales

**En salud:** Un enfermero escanea el QR del monitor con la app, se autentica con su huella, y ve los signos vitales (oxígeno en sangre, frecuencia respiratoria, alertas) directamente en su campo de visión. **El HUD no tiene cámara — puede entrar a cualquier sala sin violar políticas de privacidad del hospital.**

**En el auto:** El conductor escanea el QR del tablero con la app y ve RPM, temperatura del motor, nivel de combustible y alertas mecánicas superpuestos sobre la ruta, como un heads-up display de avión de combate.

**En infraestructura IT:** Un técnico camina por un datacenter y escanea el QR de cada servidor con la app para ver instantáneamente CPU, memoria, costos cloud y alertas — sin abrir ninguna consola ni laptop. **Sin cámara visible, el HUD pasa los controles de seguridad del datacenter.**

**En la industria:** Un operario escanea el QR de una prensa hidráulica y ve presión, temperatura, ciclos completados y alertas de mantenimiento en su campo visual.

**En el hogar:** Un QR en el termostato muestra temperatura y humedad. Sin auth — datos abiertos para el hogar.

---

## Números

| | ScouterHUD | ScouterApp | ScouterBridge | ScouterGauntlet (opcional) |
|---|---|---|---|---|
| **Costo** | ~$40-45 | Gratis (tu celular) | ~$8-15 | ~$15 |
| **Procesador** | Raspberry Pi Zero 2W | Tu smartphone | ESP32-S3 | ESP32-S3 |
| **Batería** | 5-10 horas | Tu celular | Alimentado por dispositivo | 5-7 días |
| **Conexión** | WiFi + BT | BLE/WiFi → HUD | WiFi → HUD | BLE → HUD |
| **Peso** | ~120g (sin cámara) | Tu celular + strap | ~15-25g | ~30g |
| **Cámara** | No (privacidad) | Sí (escaneo QR) | — | — |

**Ecosistema estándar (HUD + App + Bridge): ~$48-60 USD**
**Con Gauntlet opcional: +$15 USD**
**Con módulo de cámara opcional en HUD: +$12-17 USD** (ver [camera-tech-doc.md](camera-tech-doc.md))

---

## ¿Por qué open source?

Todo es público: el hardware (modelos 3D, esquemáticos, PCBs), el software (Python, C++, firmware), el protocolo QR-Link, y la documentación completa. Cualquiera puede construir su propio ScouterHUD, mejorar el diseño, o crear plugins para nuevos dispositivos.

Creemos que la mejor forma de que QR-Link se convierta en un estándar es que sea de todos, no de una empresa. Si el protocolo es abierto, los fabricantes lo adoptan sin miedo a lock-in. Si el hardware es abierto, la comunidad lo mejora más rápido que cualquier equipo interno. Y si el proyecto demuestra capacidad técnica real, eso vale más que cualquier certificación.

---

## Estado actual

El proyecto está en desarrollo activo. El software del HUD está funcional end-to-end en desktop: emulador de 5 dispositivos, 6 layouts especializados, sistema de input, auth PIN, multi-device switching, y 116 unit tests. El HUD es un **dispositivo puro de display** — sin cámara, por privacidad. El escaneo QR y la autenticación biométrica se hacen desde la ScouterApp. El siguiente paso es la ScouterApp (PoC con WebSocket) y el primer prototipo óptico cuando llegue el hardware.

---

*ScouterHUD es un proyecto de Ger. Seguí el desarrollo en GitHub y LinkedIn.*
