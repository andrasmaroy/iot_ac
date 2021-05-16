# iot_ac

Control Midea split AC unit through Home Assistant with a Raspberry Pi.

## Components

* Midea AC unit with R51M remote
* Raspberry Pi with 40-pin GPIO
* USB WiFi adapter for older Pis
* [Anavi Infrared pHAT](https://www.crowdsupply.com/anavi-technology/infrared-phat) with HTU21D sensor
* Home Assistant
* MQTT broker of choice

To get started install the pHAT along with the sensor to the Pi. The IR leds should have line of sight of the split unit, but the signals can bounce off walls pretty good.

## Installation

### Preparing the SD card

Insert the SD card and find its ID with `diskutil list` then run [prepare-sdcard.sh](prepare-sdcard.sh) to install Raspbian on it:
```sh
./prepare-sdcard.sh /dev/disk3
```

### Install dependencies & prepare the project

There are a few steps to get everything ready, first install dependencies:
```sh
pipenv install
pipenv run ansible-galaxy collection install community.general
```

Then populate the required secret files in the `secrets` folder:
* `iot_ac-mqtt-password` - password for the mqtt connection
* `domain` - domain for your network (e.g. `home.local`), this gets appended to `mqtt_domain` to get FQDN
* `password` - new password for the `pi` user on the Raspberry

### Installing on the Pi

Boot up the Raspberry and follow the steps from the end of the script to set up SSH.

When Ansible and SSH are both ready software can be installed by running the playbook:
```sh
pipenv run ansible-playbook -i hosts -l iot_ac site.yml
```

### Home Assistant

The way the code communicates with Home Assistant assumes that [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) is enabled and presents as two [sensors](https://www.home-assistant.io/integrations/sensor.mqtt/) and a [climate](https://www.home-assistant.io/integrations/climate/) unit.

### MQTT

In the background to get all entities in Home Assistant offline when the device disconnects from the network there is a little trickery with RabbitMQ.

Last will and testament can only be sent to one topic, but the device is responsible for 3 entities in HASS, in order to get those all offline with a single message we can the [shovel](https://www.rabbitmq.com/shovel.html) plugin with a fanout exchange. See the diagram below the setup.
```
                     ┌──────┐
                     │iot_ac│
                     └───┬──┘
                         │LWT
 MQTT Topic              │
┌────────────────────────▼──────────────────────────────┐
│homeassistant/climate/iot_ac/livingroom/availableFanout│
└───────────────────┬───────────────────────────────────┘
                    │
                    │                  queue
                    │                 ┌─────────────────────────────┐
                    │           ┌────►│homeassistant/iot_ac/fanout/A├──┐
                    │           │     └─────────────────────────────┘  │
 Fanout exchange    │           │      queue                           │
┌───────────────────▼───────┐   │     ┌─────────────────────────────┐  │shovel
│homeassistant/iot_ac/fanout├───┼────►│homeassistant/iot_ac/fanout/H├──┼─┐
└───────────────────────────┘   │     └─────────────────────────────┘  │ │
                                │      queue                           │ │
                                │     ┌─────────────────────────────┐  │ │
                                └────►│homeassistant/iot_ac/fanout/T├──┼─┼─┐
                                      └─────────────────────────────┘  │ │ │
                                                                       │ │ │
                   MQTT Topic                                          │ │ │
                  ┌─────────────────────────────────────────────────┐  │ │ │
             ┌────┤homeassistant/climate/iot_ac/livingroom/available│◄─┘ │ │
             │    └─────────────────────────────────────────────────┘    │ │
             │     MQTT Topic                                            │ │
 ┌────┐      │    ┌─────────────────────────────────────────────────┐    │ │
 │hass│◄─────┼────┤homeassistant/sensor/iot_ac/livingroomT/available│◄───┘ │
 └────┘      │    └─────────────────────────────────────────────────┘      │
             │     MQTT Topic                                              │
             │    ┌─────────────────────────────────────────────────┐      │
             └────┤homeassistant/sensor/iot_ac/livingroomH/available│◄─────┘
                  └─────────────────────────────────────────────────┘
```
For creating this setup in RabbitMQ see [rabbitmq_definitions.json](rabbitmq_definitions.json).

## Decoding the remote

Details about decoding from [Gabriel Oliveira](https://github.com/gabaloliveira/lirc-conf-midea-rg70a-bgef.1-2)
<details>
  <summary>Decoding the remote</summary>

## Decoding
Normal remotes (TV, Blu-Ray Players, etc...) send just one signal for each key pressed.
However, A/C remotes need to display info about the A/C current state, which are
stored in it and can be changed even if the A/C is out of reach. So the remote
needs to send all parameters (temperature, current mode, fan speed, etc...)
to avoid synchronization problems.

The code for Midea AC is (in hex):

`0x s F s 0 t m t m`

Second digit is always `F`, fourth digit is always `0`.
They MAY have something to do with fan direction and/or energy settings,
as I didn't have the time to decode them yet.


### 1st and 3rd digits (s): Fan Speed
```
1 E - auto (on modes where fan speed can only be "auto" - auto, dry)
B 4 - Auto
9 6 - Low
5 A - Med
3 C - High
```

### 5th and 7th digits (t): Temperature
```
0 F - 17°C
1 E - 18°C
3 C - 19°C
2 D - 20°C
6 9 - 21°C
7 8 - 22°C
5 A - 23°C
4 B - 24°C
C 3 - 25°C
D 2 - 26°C
9 6 - 27°C
8 7 - 28°C
A 5 - 29°C
B 4 - 30°C
```

### 6th and 8th digits (m): Mode
```
8 7 - Auto
0 F - Cool
4 B - Dry/Fan (Fan Speed tells them apart)
C 3 - Heat
```

Examples:
```
17°C, cool, low
0x9F6000FF

23°C, heat, auto
0xBF405CA3
```
</details>

## Ackowledgements

* [Gabriel Oliveira](https://github.com/gabaloliveira/lirc-conf-midea-rg70a-bgef.1-2) and [NikolaV](https://github.com/nikolav88/midea-r51m-ac-remote-lirc-raw) for the Midea Lirc configs
* [Patch for Lirc for Raspberry Pi](https://github.com/neuralassembly/raspi/blob/master/lirc-gpio-ir-0.10.patch)
