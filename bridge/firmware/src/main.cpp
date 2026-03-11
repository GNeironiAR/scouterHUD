// ScouterBridge — Fase 2: WiFi + MQTT publish (datos dummy)
// Objetivo: reemplazar el emulador Python con el ESP32 publicando el mismo JSON
// Topic: vehicles/car001/obd2  — identico al emulador, el HUD no nota la diferencia

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config_local.h"  // WiFi + MQTT credentials — not in git

// ── Configuracion ──────────────────────────────────────────────────────────────
#define LED_PIN         21
#define MQTT_PORT       1883
#define MQTT_CLIENT_ID  "scouter-bridge-001"
#define DATA_TOPIC      "vehicles/car001/obd2"
#define META_TOPIC      "vehicles/car001/obd2/$meta"
#define PUBLISH_MS      500   // 2 Hz — igual que el emulador

// ── MQTT client ────────────────────────────────────────────────────────────────
WiFiClient   net;
PubSubClient mqtt(net);

// ── Estado dummy (simula city_driving) ─────────────────────────────────────────
float rpm        = 2000;
float speed_kmh  = 40;
float coolant    = 88.0;
float fuel       = 65.0;
float battery    = 14.1;

// ── LED helpers ────────────────────────────────────────────────────────────────
void ledBlink(int times, int ms = 100) {
    for (int i = 0; i < times; i++) {
        digitalWrite(LED_PIN, HIGH); delay(ms);
        digitalWrite(LED_PIN, LOW);  delay(ms);
    }
}

// ── WiFi ───────────────────────────────────────────────────────────────────────
void connectWiFi() {
    Serial.printf("Conectando a WiFi '%s'", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        digitalWrite(LED_PIN, !digitalRead(LED_PIN));  // parpadeo lento mientras conecta
    }
    digitalWrite(LED_PIN, LOW);
    Serial.printf("\nWiFi OK — IP: %s\n", WiFi.localIP().toString().c_str());
    ledBlink(3, 100);  // 3 blinks rapidos = WiFi OK
}

// ── MQTT $meta (retained) ──────────────────────────────────────────────────────
void publishMeta() {
    // Misma estructura que emulator/devices/base.py + vehicle_obd2.py schema()
    StaticJsonDocument<512> meta;
    meta["v"]          = 1;
    meta["id"]         = "car-001";
    meta["name"]       = "Mi Auto - Honda CR-V 2010";
    meta["type"]       = "vehicle.obd2";
    meta["icon"]       = "car";
    meta["refresh_ms"] = PUBLISH_MS;
    meta["layout"]     = "auto";

    JsonObject schema = meta.createNestedObject("schema");
    JsonObject rpm_s = schema.createNestedObject("rpm");
        rpm_s["unit"] = "RPM"; rpm_s["range"][0] = 0; rpm_s["range"][1] = 8000;
        rpm_s["alert_above"] = 6000;
    JsonObject spd_s = schema.createNestedObject("speed_kmh");
        spd_s["unit"] = "km/h"; spd_s["range"][0] = 0; spd_s["range"][1] = 250;
    JsonObject clt_s = schema.createNestedObject("coolant_temp_c");
        clt_s["unit"] = "°C"; clt_s["range"][0] = 60; clt_s["range"][1] = 130;
        clt_s["alert_above"] = 110;
    JsonObject fuelS = schema.createNestedObject("fuel_pct");
        fuelS["unit"] = "%"; fuelS["range"][0] = 0; fuelS["range"][1] = 100;
        fuelS["alert_below"] = 10;
    JsonObject batS = schema.createNestedObject("battery_v");
        batS["unit"] = "V"; batS["range"][0] = 11; batS["range"][1] = 15;
        batS["alert_below"] = 12;

    char buf[512];
    serializeJson(meta, buf);
    mqtt.publish(META_TOPIC, buf, true);  // retained = true
    Serial.println("$meta publicado (retained)");
}

// ── MQTT connect ───────────────────────────────────────────────────────────────
void connectMQTT() {
    Serial.printf("Conectando a MQTT %s:%d", MQTT_BROKER, MQTT_PORT);
    while (!mqtt.connected()) {
        if (mqtt.connect(MQTT_CLIENT_ID)) {
            Serial.println(" OK");
            publishMeta();
            ledBlink(5, 60);  // 5 blinks rapidos = MQTT OK
        } else {
            Serial.printf(" fallo (rc=%d), reintentando...\n", mqtt.state());
            delay(2000);
        }
    }
}

// ── Datos dummy (city_driving) ─────────────────────────────────────────────────
void updateDummy() {
    // Variacion aleatoria simple — imita SignalGenerator del emulador
    rpm       += random(-150, 150);
    rpm        = constrain(rpm, 700, 4500);
    speed_kmh += random(-5, 5);
    speed_kmh  = constrain(speed_kmh, 0, 120);
    coolant   += random(-10, 10) * 0.05f;
    coolant    = constrain(coolant, 60, 110);
    fuel      -= 0.001f;  // consume lentamente
    fuel       = constrain(fuel, 0, 100);
    battery   += random(-5, 5) * 0.01f;
    battery    = constrain(battery, 12.0f, 15.0f);
}

// ── Publish data ───────────────────────────────────────────────────────────────
void publishData() {
    updateDummy();

    StaticJsonDocument<256> data;
    data["ts"]             = (int)(millis() / 1000);
    data["rpm"]            = (int)rpm;
    data["speed_kmh"]      = (int)speed_kmh;
    data["coolant_temp_c"] = round(coolant * 10) / 10.0f;
    data["fuel_pct"]       = round(fuel * 10) / 10.0f;
    data["battery_v"]      = round(battery * 100) / 100.0f;
    JsonArray dtcs = data.createNestedArray("dtc_codes");
    // Sin DTCs en dummy (P0171/P0420 se agregan en Fase 3A con datos reales)

    char buf[256];
    serializeJson(data, buf);
    mqtt.publish(DATA_TOPIC, buf);
    Serial.printf("→ rpm=%d spd=%d cool=%.1f fuel=%.1f bat=%.2f\n",
        (int)rpm, (int)speed_kmh, coolant, fuel, battery);
}

// ── Setup / Loop ───────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    delay(1000);
    pinMode(LED_PIN, OUTPUT);
    Serial.println("\nScouterBridge v0.2 — Fase 2 WiFi+MQTT");

    mqtt.setServer(MQTT_BROKER, MQTT_PORT);
    mqtt.setBufferSize(512);

    connectWiFi();
    connectMQTT();
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi perdido, reconectando...");
        connectWiFi();
    }
    if (!mqtt.connected()) {
        connectMQTT();
    }
    mqtt.loop();

    static unsigned long lastPublish = 0;
    if (millis() - lastPublish >= PUBLISH_MS) {
        lastPublish = millis();
        publishData();
    }
}
