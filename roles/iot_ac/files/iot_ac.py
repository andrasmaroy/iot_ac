import json
import os
import paho.mqtt.client as mqtt
import signal
import ssl
import sys
import systemd.daemon
import threading

from pconf import Pconf
from sensor import HTU21D
from time import sleep


acState = {"temp": 21, "mode": "off", "fan": "auto"}
acModeMap = {
    "auto": "AUTO",
    "cool": "COOL",
    "heat": "HEAT",
    "dry": "DRY",
    "fan_only": "FAN",
}
acFanMap = {
    "auto": "AUTO",
    "low": "LOW",
    "medium": "MED",
    "high": "HIGH"
}

Pconf.file('/etc/iot_ac/config.json', encoding='json')
config = Pconf.get()


def on_publish(client, userdata, mid):
    print("Message Published...")


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    if rc == 0:
        systemd.daemon.notify('READY=1')
        announce_device(client)
        client.subscribe("homeassistant/climate/iot_ac/livingroom/targetTempCmd")
        client.subscribe("homeassistant/climate/iot_ac/livingroom/thermostatModeCmd")
        client.subscribe("homeassistant/climate/iot_ac/livingroom/fanModeCmd")
        global should_run
        should_run = True
        client.subscribe("homeassistant/status")
        if not publish_thread.is_alive():
            publish_thread.start()


def announce_device(client):
    configuration = {
        "device_class": "temperature",
        "name": "Temperature",
        "availability_topic": "homeassistant/sensor/iot_ac/livingroomT/available",
        "state_topic": "homeassistant/sensor/iot_ac/livingroom/state",
        "unit_of_measurement": "°C",
        "value_template": "{{ value_json.temperature}}",
        "unique_id": "livingroomtempsensor1",
        "expire_after": 60,
    }
    client.publish(
        "homeassistant/sensor/iot_ac/livingroomT/config", json.dumps(configuration)
    )
    configuration = {
        "device_class": "humidity",
        "name": "Humidity",
        "availability_topic": "homeassistant/sensor/iot_ac/livingroomH/available",
        "state_topic": "homeassistant/sensor/iot_ac/livingroom/state",
        "unit_of_measurement": "%",
        "value_template": "{{ value_json.humidity}}",
        "unique_id": "livingroomhumsensor1",
        "expire_after": 60,
    }
    client.publish(
        "homeassistant/sensor/iot_ac/livingroomH/config", json.dumps(configuration)
    )
    client.publish("homeassistant/sensor/iot_ac/livingroomT/available", "online")
    client.publish("homeassistant/sensor/iot_ac/livingroomH/available", "online")

    configuration = {
        "name": "Living Room",
        "mode_command_topic": "homeassistant/climate/iot_ac/livingroom/thermostatModeCmd",
        "mode_state_topic": "homeassistant/climate/iot_ac/livingroom/state",
        "mode_state_template": "{{ value_json.mode }}",
        "availability_topic": "homeassistant/climate/iot_ac/livingroom/available",
        "temperature_command_topic": "homeassistant/climate/iot_ac/livingroom/targetTempCmd",
        "temperature_state_topic": "homeassistant/climate/iot_ac/livingroom/state",
        "temperature_state_template": "{{ value_json.temp }}",
        "current_temperature_topic": "homeassistant/sensor/iot_ac/livingroom/state",
        "fan_mode_command_topic": "homeassistant/climate/iot_ac/livingroom/fanModeCmd",
        "fan_mode_state_topic": "homeassistant/climate/iot_ac/livingroom/state",
        "fan_mode_state_template": "{{ value_json.fan }}",
        "current_temperature_template": "{{ value_json.temperature}}",
        "min_temp": "17",
        "max_temp": "30",
        "temp_step": "1.0",
        "device": {
            "manufacturer": "Midea",
            "model": "MS0A-09HRN1",
            "via_device": "iot_ac",
            "identifiers": "C101316172111311120478"
        },
        "unique_id": "livingroomac1",
        "retain": "true"
    }
    client.publish(
        "homeassistant/climate/iot_ac/livingroom/config", json.dumps(configuration)
    )
    client.publish("homeassistant/climate/iot_ac/livingroom/available", "online")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Message received for topic '{}' with payload '{}'".format(msg.topic, msg.payload))
    if msg.topic == "homeassistant/status":
        handle_hass_status(client, msg)
        return
    if msg.topic == "homeassistant/climate/iot_ac/livingroom/targetTempCmd":
        acState["temp"] = int(float(msg.payload.decode('ascii')))
    if msg.topic == "homeassistant/climate/iot_ac/livingroom/thermostatModeCmd":
        acState["mode"] = msg.payload.decode('ascii')
    if msg.topic == "homeassistant/climate/iot_ac/livingroom/fanModeCmd":
        acState["fan"] = msg.payload.decode('ascii')

    command = ""
    if acState["mode"] == "off":
        command = "off"
    else:
        if acState["mode"] == "auto" or acState["mode"] == "dry":
            acState["fan"] = "auto"
        elif acState["mode"] == "fan_only":
            acState["temp"] = 17
        command = "{}_{}_{}".format(acState["temp"], acModeMap[acState["mode"]], acFanMap[acState["fan"]])
    print("New state: {}".format(acState))
    if msg.retain != 1:
        os.system("irsend SEND_ONCE mideaAC {}".format(command))

    client.publish(
        "homeassistant/climate/iot_ac/livingroom/state",
        json.dumps(acState)
    )


def handle_hass_status(client, msg):
        global should_run
        if msg.payload.decode('ascii') == "online":
            if should_run:
                return
            else:
                announce_device(client)
                should_run = True
        else:
            if should_run:
                should_run = False
            else:
                return


def on_disconnect(client, userdata, rc):
    print("Disconnected with result code {}".format(rc))
    global should_run
    should_run = False


def publish_loop():
    global should_run
    while True:
        if should_run:
            client.publish("homeassistant/sensor/iot_ac/livingroomT/available", "online")
            client.publish("homeassistant/sensor/iot_ac/livingroomH/available", "online")
            client.publish("homeassistant/climate/iot_ac/livingroom/available", "online")

            h, t = htu.all()
            client.publish(
                "homeassistant/sensor/iot_ac/livingroom/state",
                json.dumps({"temperature": round(t.C, 1), "humidity": round(h.RH, 1)}),
            )
            client.publish(
                "homeassistant/climate/iot_ac/livingroom/state",
                json.dumps(acState)
            )
            sleep(15)


def signal_handler(signum, frame):
    global should_run
    should_run = False
    print("Shutting down")
    client.publish("homeassistant/sensor/iot_ac/livingroomT/available", "offline").wait_for_publish()
    client.publish("homeassistant/sensor/iot_ac/livingroomH/available", "offline").wait_for_publish()
    client.publish("homeassistant/climate/iot_ac/livingroom/available", "offline").wait_for_publish()
    client.loop_stop()
    client.disconnect()
    print("Disconnected and loop stopped")
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)
publish_thread = threading.Thread(target=publish_loop, daemon=True)
htu = HTU21D(1, 0x40)
should_run = False

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_disconnect = on_disconnect
client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
client.will_set("homeassistant/climate/iot_ac/livingroom/availableFanout", "offline")

client.username_pw_set(config["user"], config["password"])
client.connect(config["host"], config["port"], 60)
client.loop_forever()
