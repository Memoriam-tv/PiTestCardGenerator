#!/usr/bin/env bash
# Install piclock to /opt/piclock and enable the systemd unit.
# Idempotent; run with sudo on the Raspberry Pi.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$(id -u)" -ne 0 ]; then
    echo "run with sudo: sudo bash deploy/install.sh" >&2
    exit 1
fi

apt-get update
apt-get install -y python3-pygame fonts-dejavu-core libegl1 libgles2 libgbm1 rsync

install -d /opt/piclock
rsync -a --delete "$REPO/piclock" /opt/piclock/

install -m644 "$REPO/deploy/piclock.service" /etc/systemd/system/piclock.service
systemctl daemon-reload
systemctl enable --now piclock.service

cat <<'EOF'

piclock installed. Three system tweaks are manual (see README.md):

  1. boot to console, no desktop:
       sudo raspi-config nonint do_boot_behaviour B1
  2. KMS driver in /boot/firmware/config.txt (Bookworm default):
       dtoverlay=vc4-kms-v3d
  3. stop console blanking: append to /boot/firmware/cmdline.txt
       consoleblank=0

Also make sure the timezone and NTP are right:
       sudo timedatectl set-timezone Europe/Amsterdam
       sudo timedatectl set-ntp true
EOF
