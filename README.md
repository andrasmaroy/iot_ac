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
