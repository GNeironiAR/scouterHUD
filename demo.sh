#!/bin/bash
# ScouterHUD Demo Launcher — corre en el Pi Zero 2W
#
# Uso:
#   ./demo.sh --broker 192.168.1.87
#   ./demo.sh --broker 192.168.1.87 --rotation 2
#   ./demo.sh --wifi "SSID" "password" --broker 192.168.1.87
#
# Requisitos:
#   - Pi con ScouterHUD instalado (ver docs/pi-setup-guide.md)
#   - Broker MQTT corriendo en otra maquina (PC, servidor, etc)
#   - Celular con ScouterApp en la misma red WiFi

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROTATION=0
MIRROR=""
BROKER=""
WIFI_SSID=""
WIFI_PASS=""

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --wifi)
            WIFI_SSID="$2"
            WIFI_PASS="$3"
            shift 3
            ;;
        --broker)
            BROKER="$2"
            shift 2
            ;;
        --rotation)
            ROTATION="$2"
            shift 2
            ;;
        --mirror)
            MIRROR="--mirror"
            shift
            ;;
        --help|-h)
            echo "Uso: ./demo.sh --broker <IP> [--wifi SSID PASSWORD] [--rotation 0-3] [--mirror]"
            echo ""
            echo "Opciones:"
            echo "  --broker IP       IP del broker MQTT (requerido)"
            echo "  --wifi SSID PASS  Conectar a otra red WiFi antes de iniciar"
            echo "  --rotation N      Rotacion del display (0=normal, 2=180)"
            echo "  --mirror          Espejo horizontal (para beam splitter)"
            echo ""
            echo "Ejemplo:"
            echo "  ./demo.sh --broker 192.168.1.87"
            echo "  ./demo.sh --wifi \"HackathonWiFi\" \"pass123\" --broker 10.0.0.5"
            exit 0
            ;;
        *)
            echo "Argumento desconocido: $1"
            echo "Usa --help para ver opciones"
            exit 1
            ;;
    esac
done

if [ -z "$BROKER" ]; then
    echo "Error: --broker es requerido"
    echo "Uso: ./demo.sh --broker <IP-del-broker>"
    exit 1
fi

# --- WiFi (opcional) ---
if [ -n "$WIFI_SSID" ]; then
    echo "Conectando a WiFi: $WIFI_SSID ..."
    sudo nmcli dev wifi connect "$WIFI_SSID" password "$WIFI_PASS" && echo "WiFi OK" || {
        echo "Error conectando a WiFi. Verificar SSID y password."
        exit 1
    }
    sleep 3
fi

# --- Mostrar IP ---
PI_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "====================================="
echo "  ScouterHUD Demo"
echo "====================================="
echo "  Pi IP:    $PI_IP"
echo "  Broker:   $BROKER:1883"
echo "  Rotation: $ROTATION${MIRROR:+ (mirrored)}"
echo "  App:      ws://$PI_IP:8765"
echo "====================================="
echo ""
echo "Conecta la ScouterApp a: ws://$PI_IP:8765"
echo "Ctrl+C para detener"
echo ""

# --- Levantar HUD ---
cd "$SCRIPT_DIR/software"
PYTHONPATH=. ../.venv/bin/python run_hud.py --spi --phone --rotation "$ROTATION" $MIRROR
