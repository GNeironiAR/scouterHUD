# ADR-001: Cámara removida del HUD base — módulo opcional

**Estado:** Aceptada
**Fecha:** Febrero 2026
**Autor:** Ger
**Afecta a:** ScouterHUD, ScouterApp, BOM, costos, diseño mecánico

---

## Contexto

El diseño original del ScouterHUD (TECH_DESIGN v0.1-v0.2) incluía una Pi Camera OV5647 integrada en el HUD como componente obligatorio. La cámara se usaba para escanear QR codes de dispositivos IoT (protocolo QR-Link) y era el único método de input para descubrir dispositivos.

Durante el desarrollo, se identificaron problemas fundamentales con esta decisión:

1. **Rechazo social ("Glassholes effect"):** Google Glass demostró que un wearable con cámara visible genera desconfianza inmediata. Las personas alrededor asumen que están siendo grabadas.

2. **Restricciones de acceso:** Hospitales (HIPAA), juzgados, datacenters, laboratorios y fábricas prohíben dispositivos con cámara. Un HUD con cámara no puede entrar a los espacios donde más se necesita.

3. **Regulaciones legales:** HIPAA, GDPR, y legislación local en múltiples países restringen la grabación no consentida. Un wearable con cámara "siempre presente" está en zona gris legal permanente.

4. **Complejidad y costo innecesarios:** La Pi Camera sumaba ~$12-17 al costo, cable flex, montaje mecánico, configuración de GPU, y ~3g de peso adicional — todo para una función que el celular del usuario ya puede hacer mejor.

---

## Decisión

**La cámara se remueve del ScouterHUD base y pasa a ser un módulo opcional separado.**

El escaneo de QR codes se delega a la ScouterApp (celular del usuario), que envía la URL al HUD por BLE/WiFi. El HUD se convierte en un **dispositivo puro de display**.

---

## Razones

### Privacidad (razón principal)

- Sin cámara, el HUD puede entrar a cualquier espacio sin restricciones
- No hay ambigüedad sobre si el usuario está grabando — el HUD es solo un display
- El escaneo con el celular es **intencional** — el usuario activamente apunta y escanea, no hay captura pasiva
- Se eliminan todas las preocupaciones HIPAA/GDPR del wearable

### Costo

| Configuración | Costo HUD |
|---|---|
| HUD base (sin cámara) | **~$40-45** |
| HUD con cámara opcional | ~$55-60 |

Ahorro de ~$12-17 por unidad en la configuración estándar.

### Simplicidad

- Menos hardware: sin cable flex, sin montaje de cámara, sin LED indicador
- Menos software: sin picamera2, sin asignación de GPU, sin procesamiento de imagen
- Menos peso: 120g vs 153g (originalmente con cámara)
- Menos puntos de fallo en el diseño mecánico

### El celular ya es mejor

- La cámara del celular tiene mejor resolución, autofoco, y procesamiento de imagen que cualquier Pi Camera
- El celular ya tiene biometría (FaceID/huella) que reemplaza la entrada manual de PIN
- Costo adicional de cámara en el celular: $0

---

## Implicancias

### Positivas

1. **Acceso universal:** El HUD puede usarse en hospitales, juzgados, datacenters y cualquier espacio que prohíba cámaras
2. **Menor costo base:** ~$40-45 vs ~$55-60 (ahorro del 20-25%)
3. **Menor complejidad:** Menos componentes, menos configuración, menos puntos de fallo
4. **Mejor percepción social:** El usuario no tiene que explicar que "la cámara no está grabando"
5. **HUD más liviano:** 120g vs 153g

### Negativas / Trade-offs

1. **Requiere la ScouterApp:** Sin la app, no hay forma de escanear QR codes. El HUD puede recibir dispositivos por CLI (`--demo`) pero no escanear nuevos en campo sin la app
2. **Un paso extra:** El usuario debe levantar el brazo y apuntar el celular al QR, en vez de simplemente mirar el QR a través del HUD
3. **No hands-free al 100%:** El escaneo de QR requiere interacción con el celular (aunque la visualización posterior sí es hands-free)

### Mitigaciones

- **Fallback CLI:** Para desarrollo y demos, `--demo` permite conectar a dispositivos sin QR scan
- **Módulo de cámara opcional:** Documentado en [camera-tech-doc.md](camera-tech-doc.md) para los edge cases que lo requieran
- **Escaneo rápido:** La ScouterApp auto-detecta QR codes sin presionar botón — apuntar y listo

---

## Alternativas consideradas

### 1. Mantener la cámara como obligatoria (RECHAZADA)

- Pros: Escaneo hands-free, una menos dependencia del celular
- Contras: Todos los problemas de privacidad y acceso descritos arriba
- Razón del rechazo: Los problemas de privacidad son fundamentales y no se resuelven con mitigaciones técnicas

### 2. Cámara con obturador físico (RECHAZADA)

- Pros: El usuario puede cerrar físicamente la cámara cuando no se usa
- Contras: No resuelve la percepción — las personas ven el hardware de cámara y asumen lo peor. Los espacios restringidos prohíben el hardware, no importa si está "apagado"
- Razón del rechazo: La percepción social y las regulaciones no distinguen entre cámara activa e inactiva

### 3. Cámara con LED hardwired indicador (CONSIDERADA para el módulo opcional)

- Pros: LED que no se puede desactivar por software indica claramente cuando la cámara está activa
- Contras: No resuelve el problema de acceso a espacios restringidos
- Estado: **Adoptada para el módulo de cámara opcional.** Si alguien agrega la cámara, el LED hardwired es obligatorio

### 4. Sin cámara, sin app — solo input manual (RECHAZADA)

- Pros: Máxima simplicidad
- Contras: Conectar dispositivos sería un proceso tedioso (ingresar URLs manualmente)
- Razón del rechazo: La experiencia de usuario sería inaceptable

---

## Documentos relacionados

- [camera-tech-doc.md](camera-tech-doc.md) — Diseño técnico del módulo de cámara opcional
- [app-tech-doc.md](app-tech-doc.md) — ScouterApp como reemplazo del escaneo directo
- [ADR-002: ScouterApp como input principal](adr-002-app-primary-input.md)
- [TECH_DESIGN.md](TECH_DESIGN.md) — Diseño técnico general (v0.3+)
