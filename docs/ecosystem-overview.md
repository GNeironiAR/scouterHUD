# ScouterHUD — Un ecosistema wearable que te permite ver los datos de cualquier dispositivo con solo mirarlo

---

## La idea en una frase

**¿Y si pudieras mirar cualquier dispositivo — tu auto, un monitor médico, un servidor, un sensor — y ver sus datos flotando frente a tu ojo en tiempo real?**

ScouterHUD es un ecosistema open source de tres dispositivos que hacen exactamente eso, por menos de $85 USD.

---

## Cómo funciona

El concepto es simple: cada dispositivo del mundo real tiene un pequeño código QR pegado. Cuando el usuario mira ese QR a través del ScouterHUD, el sistema se conecta automáticamente al dispositivo y muestra sus datos en vivo frente a su ojo, superpuestos sobre el mundo real. Sin tocar nada. Sin pantallas. Manos libres.

```
   Lo que ves                    Lo que pasa

   Mirás un QR en              La cámara del HUD
   un monitor ──────────────►  lo detecta y se
   médico                      conecta al dispositivo

   En tu ojo aparecen          Los datos viajan
   los signos vitales ◄──────  por WiFi hasta
   del paciente                tu display
   
   Tocás tu brazalete          El Gauntlet envía
   para confirmar   ──────────► el comando al HUD
   una acción                  sin decir nada
```

---

## Los tres dispositivos

### 1. ScouterHUD — Los ojos (~$55 USD)

Una vincha con una pantalla semitransparente frente al ojo derecho. Inspirado en el scouter de Vegeta de Dragon Ball Z.

**Qué hace:**
- Muestra datos superpuestos sobre tu visión real (ves el mundo + información al mismo tiempo)
- Tiene una cámara que escanea códigos QR para conectarse a dispositivos
- Incluye micrófono y auricular para un asistente de IA por voz
- Funciona con WiFi y Bluetooth

**Cómo se usa:**
Se pone como una vincha. La batería en la nuca hace de contrapeso. Es cómodo por horas. Pesa menos que unos auriculares over-ear (~150g).

---

### 2. ScouterGauntlet — Las manos (~$15 USD)

Un brazalete en el antebrazo con 5 pads táctiles. Inspirado en la computadora de muñeca del Predator.

**Qué hace:**
- Permite controlar el HUD sin hablar (ideal para entornos silenciosos o privados)
- Ingreso de PINs y códigos de seguridad sin decirlos en voz alta
- Navegación de menús, confirmación, cancelación
- Escritura de texto mediante combinaciones de toques (como acordes de piano)

**Cómo se usa:**
Se lleva en el antebrazo opuesto a la mano dominante. Se opera tocando los pads con la otra mano, sin necesidad de mirar el brazalete — el feedback llega como vibración en la muñeca y visual en el HUD.

**¿Por qué no solo voz?** Porque no podés decir un código TOTP en voz alta en una oficina, ni darle instrucciones a un asistente de IA en una sala de hospital silenciosa, ni hablarle a tu dispositivo en un ambiente industrial ruidoso.

---

### 3. ScouterBridge — El traductor (~$8-15 USD)

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

**Seguridad:** Los datos sensibles (médicos, financieros) están protegidos. El QR te dice que el dispositivo existe, pero para ver sus datos necesitás autenticarte — con un PIN desde el Gauntlet, un token pre-cargado, o certificados digitales según el nivel de seguridad requerido.

---

## Casos de uso reales

**En salud:** Un enfermero mira el QR del monitor de un paciente post-operatorio y ve los signos vitales (oxígeno en sangre, frecuencia respiratoria, alertas) directamente en su campo de visión, sin dejar de atender al paciente con las manos.

**En el auto:** El conductor escanea el QR del tablero y ve RPM, temperatura del motor, nivel de combustible y alertas mecánicas superpuestos sobre la ruta, como un heads-up display de avión de combate.

**En infraestructura IT:** Un técnico camina por un datacenter y mira el QR de cada servidor para ver instantáneamente CPU, memoria, costos cloud y alertas — sin abrir ninguna consola ni laptop.

**En la industria:** Un operario mira el QR de una prensa hidráulica y ve presión, temperatura, ciclos completados y alertas de mantenimiento en su campo visual.

**En el hogar:** Un QR en el termostato muestra temperatura y humedad. Un QR en el termotanque muestra la temperatura del agua.

---

## Números

| | ScouterHUD | ScouterGauntlet | ScouterBridge |
|---|---|---|---|
| **Costo** | ~$55 | ~$15 | ~$8-15 |
| **Procesador** | Raspberry Pi Zero 2W | ESP32-S3 | ESP32-S3 |
| **Batería** | 5-10 horas | 5-7 días | Alimentado por el dispositivo |
| **Conexión** | WiFi + BT | BLE → HUD | WiFi → HUD |
| **Peso** | ~150g | ~30g | ~15-25g |

**Ecosistema completo: ~$78-85 USD**
**Solo HUD + Bridge (sin Gauntlet): ~$63-70 USD**

---

## ¿Por qué open source?

Todo es público: el hardware (modelos 3D, esquemáticos, PCBs), el software (Python, C++, firmware), el protocolo QR-Link, y la documentación completa. Cualquiera puede construir su propio ScouterHUD, mejorar el diseño, o crear plugins para nuevos dispositivos.

Creemos que la mejor forma de que QR-Link se convierta en un estándar es que sea de todos, no de una empresa. Si el protocolo es abierto, los fabricantes lo adoptan sin miedo a lock-in. Si el hardware es abierto, la comunidad lo mejora más rápido que cualquier equipo interno. Y si el proyecto demuestra capacidad técnica real, eso vale más que cualquier certificación.

---

## Estado actual

El proyecto está en desarrollo activo. El emulador de dispositivos ya funciona (simula 5 tipos de dispositivos publicando datos realistas por MQTT). El siguiente paso es el display emulador en desktop para desarrollar el software sin necesitar el hardware físico, seguido del primer prototipo óptico para validar que la pantalla semitransparente es legible y cómoda.

---

*ScouterHUD es un proyecto de Ger. Seguí el desarrollo en GitHub y LinkedIn.*
