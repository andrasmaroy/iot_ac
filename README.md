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

### Installing on the Pi

Designed to be used as an Ansible role included in a playbook. To install include in the `requirements.yml` like so:
```yml
collections:
  - name: git@github.com:andrasmaroy/iot_ac.git#/ansible
    type: git
```
And in the playbook file for the appropriate hosts:
```yml
- hosts: iot_ac
  collections:
    - andrasmaroy.iot_ac
  tasks:
    - import_role:
        name: iot_ac
```
Presented as a collection so that it can be installed directly from the [ansible](ansible) subfolder of this repo.

#### Configuration

The following Ansible vars are available for configuration:

`mqtt_host` (**required**): Hostname of the MQTT host to connect to

`mqtt_port` (default: 1883): Port to use for MQTT connection

`mqtt_user` (default: iot_ac): MQTT username

`mqtt_password` (**required**): MQTT password

### Home Assistant

The way the code communicates with Home Assistant assumes that [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) is enabled and presents as two [sensors](https://www.home-assistant.io/integrations/sensor.mqtt/) and a [climate](https://www.home-assistant.io/integrations/climate/) unit.

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
