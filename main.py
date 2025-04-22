import network
import time
import ujson
import machine
import dht
import ubinascii

from machine import Pin, UART
from mqtt_simple import MQTTClient
from config import CONF as cf
from micropyGPS import MicropyGPS

gps_uart = UART(2, baudrate=9600, tx=17, rx=16)
gps = MicropyGPS(location_formatting="dd")

ssid = cf.SSID
password = cf.PASSWORD

mqtt_server = cf.MQTT_SERVER
mqtt_port = cf.MQTT_PORT
mqtt_user = cf.MQTT_USER
mqtt_password = cf.MQTT_PASSWORD

ne_id = cf.NE_ID
ne_id_str = ne_id.decode()

topic_pub = cf.TOPIC_PUB.encode()
topic_sub = cf.TOPIC_SUB.encode()

sensor = dht.DHT11(Pin(4))
rele = Pin(5, Pin.OUT)
rele.value(0)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    print("Conectando ao Wi-Fi", ssid)
    retry = 0
    while not wlan.isconnected():
        retry += 1
        if retry > 20:
            print("Falha Wi-Fi, reiniciando...")
            machine.reset()
        time.sleep(1)
    print("Wi-Fi conectado, IP:", wlan.ifconfig()[0])


def mqtt_callback(topic, msg):
    print("Mensagem recebida: ", topic.decode(), msg.decode())

    if topic == topic_sub:
        try:
            payload = ujson.loads(msg)
            ne_id_msg = payload.get("ne_id", "")

            if ne_id_msg != ne_id_str:
                print("ne_id diferente, ignorando comando.")
                return

            comando = payload.get(cf.RELE, "").upper()

            if comando == "ON":
                rele.value(1)
            elif comando == "OFF":
                rele.value(0)
            else:
                print("Comando desconhecido:", comando)

        except Exception as e:
            print("Erro ao processar mensagem JSON:", e)


def connect_mqtt():
    client = MQTTClient(ne_id, mqtt_server, mqtt_port, mqtt_user, mqtt_password)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(topic_sub)
    print("MQTT conectado:", mqtt_server)
    return client


def read_dht11():
    try:
        sensor.measure()
        return sensor.temperature(), sensor.humidity()
    except:
        return None, None


def read_gps():
    while gps_uart.any():
        for ch in gps_uart.read():
            if gps.update(chr(ch)) and gps.valid:
                lat_dd, lat_hemi = gps.latitude
                lon_dd, lon_hemi = gps.longitude
                lat = -lat_dd if lat_hemi == "S" else lat_dd
                lon = -lon_dd if lon_hemi == "W" else lon_dd
                return lat, lon
    return None, None


def main():
    connect_wifi()
    client = connect_mqtt()

    last_message = time.time()
    interval = cf.TIME

    while True:
        try:
            client.check_msg()
        except Exception as e:
            print("Erro no MQTT, reconectando...", e)
            time.sleep(2)
            client = connect_mqtt()

        if (time.time() - last_message) > interval:
            temp, umid = read_dht11()
            lat, lon = read_gps()
            status = "ON" if rele.value() == 1 else "OFF"

            if temp is None or umid is None:
                print("Leitura inválida do DHT11. Pulando envio.")
                continue

            payload = {
                "cliente": mqtt_user,
                "ne_id": ne_id_str,
                "temperatura": temp,
                "umidade": umid,
                "rele": status,
            }

            if lat is not None and lon is not None:
                payload["latitude"] = lat
                payload["longitude"] = lon

            try:
                client.publish(topic_pub, ujson.dumps(payload))
                print("Dados publicados:", payload)
            except Exception as e:
                print("Erro ao publicar no MQTT:", e)
                client = connect_mqtt()

            last_message = time.time()

        time.sleep(0.1)


try:
    main()
except Exception as e:
    print("Erro geral:", e)
    machine.reset()
