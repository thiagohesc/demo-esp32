import ubinascii
import network


class CONF:
    SSID = "SUA_REDE"
    PASSWORD = "SUA_SENHA"

    MQTT_SERVER = "SEU_MQTT_SERVER"
    MQTT_PORT = 1883
    MQTT_USER = "MQTT_USER"
    MQTT_PASSWORD = "MQTT_SENHA"
    MQTT_ROOT = "MQTT_ROOT"
    MQTT_PUB = "status"
    MQTT_SUB = "command"
    RELE = "rele"

    NE_DESCRIPTION = b"esp_32_"
    NE_ID = NE_DESCRIPTION + ubinascii.hexlify(network.WLAN().config("mac"))

    TOPIC_PUB = f"{MQTT_ROOT}/{MQTT_USER}/{MQTT_PUB}"
    TOPIC_SUB = f"{MQTT_ROOT}/{MQTT_USER}/{MQTT_SUB}"

    TIME = 60
