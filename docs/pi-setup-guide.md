# Pi Zero 2W — Setup Guide

Guia completa para flashear, configurar y correr ScouterHUD en el Pi Zero 2W.

---

## 1. Flash MicroSD

Usar **Raspberry Pi Imager** (Windows):

1. Dispositivo: **Raspberry Pi Zero 2 W**
2. SO: **Raspberry Pi OS Lite (64-bit)** — en "Raspberry Pi OS (other)"
3. Personalizacion:
   - Hostname: `scouterhud`
   - Usuario: `pi` + password
   - WiFi SSID: exacto, case-sensitive
   - WiFi password: real, no hasheado
   - Pais WiFi: `AR`
   - **SSH habilitado** (autenticacion por password)
4. Flashear, sacar SD, poner en Pi

**IMPORTANTE:**
- Conectar USB-C al puerto **PWR** (el del borde), NO el del medio (USB data).
- Usar **cargador de pared** (5V/2A minimo). Powerbanks pueden auto-apagarse por bajo consumo (~200mA). USB de laptop puede ser insuficiente.
- Primer boot puede demorar 5-10 min en conectar a WiFi (genera keys, expande particion).

---

## 2. Primer Boot + SSH

1. Esperar 5-10 minutos (primer boot es lento)
2. Buscar IP del Pi desde la app WiFi del celular (mDNS `.local` no funciona desde WSL2)
3. Conectar:

```bash
ssh pi@<pi-ip>
```

Si da error "REMOTE HOST IDENTIFICATION HAS CHANGED" (por reflash):
```bash
ssh-keygen -f ~/.ssh/known_hosts -R "<pi-ip>"
ssh pi@<pi-ip>
```

---

## 3. Instalar Software

```bash
# Habilitar SPI
sudo raspi-config nonint do_spi 0
ls /dev/spidev*  # debe mostrar 0.0 y 0.1

# Dependencias del sistema
sudo apt update && sudo apt install -y python3-pip python3-venv libzbar0 git

# Clonar e instalar
git clone https://github.com/GNeironiAR/scouterHUD.git
cd ~/scouterHUD
python3 -m venv .venv
cd software && ../.venv/bin/pip install -e ".[pi]"
../.venv/bin/pip install st7789

# Verificar
../.venv/bin/python -c "import st7789; print('st7789 OK')"
../.venv/bin/python -c "from scouterhud.display.backend_spi import SPIBackend; print('SPIBackend OK')"
```

---

## 4. Identificar GPIO Pins

**Comando clave** para ver el pinout en el Pi:

```bash
pinout
```

Esto muestra el diagrama oficial del board con todos los pines.

### Board del Pi Zero 2W:

```
,--oooooooooooooooooooo---.
|  1ooooooooooooooooooo J8|
---+     +---+  PiZero2W  c|
 sd|     |SoC|   Wi V1.0  s|
---+     +---+   Fi       i|
| hdmi            usb pwr |
`-|  |------------| |-| |-'
```

### Pinout (orientacion: SD arriba, USB abajo-derecha):

```
     (SD) ↑

   [1]  [2]     3V3 / 5V
   [3]  [4]     GPIO2 / 5V
   [5]  [6]     GPIO3 / GND
   [7]  [8]     GPIO4 / GPIO14
   [9]  [10]    GND / GPIO15
  [11]  [12]    GPIO17 / GPIO18
  [13]  [14]    GPIO27 / GND
  [15]  [16]    GPIO22 / GPIO23
  [17]  [18]    3V3 / GPIO24
  [19]  [20]    GPIO10(MOSI) / GND
  [21]  [22]    GPIO9 / GPIO25
  [23]  [24]    GPIO11(SCLK) / GPIO8(CE0)
  [25]  [26]    GND / GPIO7

  izq (1,3,5...) = impares = lado centro del board (cerca del SoC)
  der (2,4,6...) = pares   = lado borde de la placa
```

---

## 5. Cableado Display Seengreat ST7789 1.3" (8 pines, con cable JST)

Display: **Seengreat Xi-1.3inch LCD Display B**, ST7789, 240x240, SPI.
Modelo Amazon: X004LYZ9PD. Viene con cable JST pre-armado (8 hilos con dupont hembra).

```
Display    Color      Pi Pin    GPIO         Funcion
-------    -----      ------    -----        --------
VCC        rojo       Pin 1     3.3V         Alimentacion
GND        negro      Pin 6     GND          Tierra
DIN        amarillo   Pin 19    GPIO10       SPI MOSI (datos)
CLK        verde      Pin 23    GPIO11       SPI SCLK (reloj)
RST        blanco     Pin 13    GPIO27       Reset
DC         naranja    Pin 22    GPIO25       Data/Command
CS         azul       Pin 24    GPIO8        SPI CE0 (chip select)
BL         violeta    Pin 18    GPIO24       Backlight (PWM)
```

### Diagrama visual (SD arriba, USB abajo-derecha):

```
     (SD) ↑

 rojo(VCC) → [1]  [2]
              [3]  [4]
              [5]  [6]  ← negro(GND)
              [7]  [8]
              [9]  [10]
              [11] [12]
blanco(RST)→ [13] [14]
              [15] [16]
              [17] [18] ← violeta(BL)
amaril(DIN)→ [19] [20]
              [21] [22] ← naranja(DC)
 verde(CLK)→ [23] [24] ← azul(CS)
              [25] [26]
```

**Patron:** impares (1,13,19,23) = izquierda (centro board), pares (6,18,22,24) = derecha (borde placa).

---

## 6. Test del Display

### Test con codigo del fabricante:

```bash
# Instalar dependencias
sudo apt-get install -y python3-numpy python3-gpiozero python3-pil python3-spidev

# Clonar demo del fabricante
cd ~ && git clone https://github.com/seengreat/1.3inch-LCD-Display.git

# Correr demo
cd ~/1.3inch-LCD-Display/lgpio/python/
python3 gui_demo.py
```

Deberia mostrar figuras geometricas y una imagen de flores alternando cada 3 segundos.

### Test rapido de colores (con libreria st7789):

```bash
cd ~/scouterHUD && .venv/bin/python -c "
import st7789
from PIL import Image
import time
disp = st7789.ST7789(height=240, width=240, rotation=0, port=0, cs=0, dc=25, rst=27, backlight=24, spi_speed_hz=8000000)
disp.begin()
colors = [('ROJO', (255,0,0)), ('VERDE', (0,255,0)), ('AZUL', (0,0,255)), ('BLANCO', (255,255,255))]
for name, color in colors:
    print(f'Mostrando {name}...')
    img = Image.new('RGB', (240, 240), color)
    disp.display(img)
    time.sleep(3)
print('Fin')
"
```

---

## 7. Correr ScouterHUD

```bash
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python run_hud.py --spi --phone
```

Luego conectar ScouterApp al Pi: `ws://<pi-ip>:8765`

---

## 8. Demo Completa (3 terminales WSL2 + celular)

**Terminal 1 — Broker MQTT:**
```bash
docker run --rm -p 1883:1883 eclipse-mosquitto:2 mosquitto -c /mosquitto-no-auth.conf
```

**Terminal 2 — Emulador:**
```bash
cd ~/scouterHUD/emulator && PYTHONPATH=. ../.venv/bin/python emulator.py
```

**Terminal 3 — SSH al Pi:**
```bash
ssh pi@<pi-ip>
cd ~/scouterHUD/software && PYTHONPATH=. ../.venv/bin/python run_hud.py --spi --phone
```

**Celular — ScouterApp:**
- Conectar a `ws://<pi-ip>:8765`
- Escanear QR de un device (ej: monitor-bed-12)
- PIN para monitor-bed-12: `1234`

### Requisito: MQTT accesible desde Pi

El broker Docker en WSL2 no es accesible desde el Pi por defecto. Ejecutar en **PowerShell como Admin**:

```powershell
# Port proxy
netsh interface portproxy add v4tov4 listenport=1883 listenaddress=0.0.0.0 connectport=1883 connectaddress=localhost

# Firewall
New-NetFirewallRule -DisplayName "MQTT Broker" -Direction Inbound -Protocol TCP -LocalPort 1883 -Action Allow
```

Verificar desde el Pi:
```bash
nc -zv <pc-ip> 1883
```

### QR Codes

Los QR deben apuntar a la IP de la PC (no 0.0.0.0). Editar `emulator/config.yaml`:
```yaml
broker:
  host: "<pc-ip>"
```

Regenerar:
```bash
cd ~/scouterHUD/emulator && PYTHONPATH=. ../.venv/bin/python generate_all_qrs.py
```

---

## Problemas Conocidos

| Problema | Solucion |
|----------|----------|
| `python -m scouterhud.main --spi --phone` se cuelga en Pi | Usar `run_hud.py` en su lugar |
| Powerbank se apaga solo | Pi consume ~200mA, algunos powerbanks necesitan >500mA. Usar cargador de pared (5V/2A+) |
| SD se corrompe por corte de energia | Reflashear con Raspberry Pi Imager (ver paso 1) |
| mDNS (.local) no resuelve desde WSL2 | Usar IP directa, buscar desde app WiFi del celular |
| Display no muestra nada | 1) Verificar cableado pin por pin con `pinout`. 2) Probar demo del fabricante. 3) Verificar que SPI esta habilitado |
| SSH "REMOTE HOST IDENTIFICATION HAS CHANGED" | Borrar key vieja: `ssh-keygen -f ~/.ssh/known_hosts -R "<pi-ip>"` |
| Pi no conecta a WiFi | Usar cargador de pared (no powerbank/USB laptop). Primer boot demora 5-10 min |
| No se sabe cual es Pin 1 | Correr `pinout` en el Pi, o buscar pad cuadrado en el PCB |
