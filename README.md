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
