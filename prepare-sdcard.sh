#!/usr/bin/env bash
#
# Script that fetches the latest Raspbian image and burns it to the given
# SD card. Designed for MacOS
# Usage: ./prepare-sdcard.sh /dev/disk2

set -euo pipefail

if [ $# -lt 1 ]; then
  >&2 echo 'Usage: ./prepare-sdcard.sh /dev/diskX'
  exit 1
fi

readonly SDCARD_PATH="$1"
readonly NAME='iot_ac'

stat "${SDCARD_PATH}" &> /dev/null

cd "$(mktemp -d)"
echo "Downloading image"
wget --no-verbose --show-progress --progress=bar https://downloads.raspberrypi.org/raspbian_lite_latest
unzip raspbian_lite_latest
readonly IMAGE_FILE="$(unzip -qql raspbian_lite_latest | awk '{ print $4;}')"

echo 'Copying image to SD card'
diskutil unmountDisk "${SDCARD_PATH}"
sudo dd bs=4m if="${IMAGE_FILE}" of="${SDCARD_PATH/disk/rdisk}"
sync
sleep 5s

echo 'Mounting SD card'
diskutil mountDisk "${SDCARD_PATH}s1"
pushd /Volumes/boot > /dev/null
touch ssh
read -r -p "Wifi SSID: " WIFI_SSID
read -r -s -p "Wifi password: " WIFI_PASSWORD
cat <<EOF > wpa_supplicant.conf
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=HU

network={
        ssid="${WIFI_SSID}"
        psk="${WIFI_PASSWORD}"
}
EOF

echo 'Ejecting SD card'
popd > /dev/null
diskutil eject "${SDCARD_PATH}"

echo 'Checking SSH key'
if [ ! -e "${HOME}/.ssh/keys/personal/id_${NAME}" ]; then
  ssh-keygen -t ed25519 -f "${HOME}/.ssh/keys/personal/id_${NAME}"
fi

echo 'Setup complete, plug in the Raspberry then run:'
echo "ssh-copy-id -o PasswordAuthentication=yes -i ~/.ssh/keys/personal/id_${NAME} pi@<IP>"
echo 'Add it to ssh config:'
echo "Host iot_ac
    HostName <IP>
    User pi
    IdentityFile ~/.ssh/keys/personal/id_${NAME}"
