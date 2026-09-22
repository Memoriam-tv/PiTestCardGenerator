#!/usr/bin/env bash
# Install piclock to /opt/piclock and enable the systemd unit.
# Idempotent; run with sudo on the Raspberry Pi.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$(id -u)" -ne 0 ]; then
    echo "run with sudo: sudo bash deploy/install.sh" >&2
    exit 1
fi

DEPS="python3 python3-pygame fonts-dejavu-core rsync"

# Raspbian jessie's Release files have expired and its archive keys are gone,
# so fall back to an unauthenticated install there.
apt-get -o Acquire::Check-Valid-Until=false update || true
apt-get install -y $DEPS ||
    apt-get install -y --force-yes -o Acquire::Check-Valid-Until=false $DEPS

install -d /opt/piclock
rsync -a --delete "$REPO/piclock" /opt/piclock/
rsync -a --delete "$REPO/cards" /opt/piclock/

install -m644 "$REPO/deploy/piclock.service" /etc/systemd/system/piclock.service
systemctl daemon-reload
# systemd 215 (jessie) has no `enable --now`.
systemctl enable piclock.service
systemctl restart piclock.service

cat <<'EOF'

piclock installed. The manual system tweaks (see README.md):

  1. boot to console, no desktop:
       sudo raspi-config nonint do_boot_behaviour B1
  2. stop console blanking: append consoleblank=0 to the kernel command line
       /boot/cmdline.txt (jessie) or /boot/firmware/cmdline.txt (bookworm)
  3. SDL 2 targets (bookworm) want dtoverlay=vc4-kms-v3d in config.txt and
     SDL_VIDEODRIVER=kmsdrm in the unit; SDL 1.2 targets (jessie) use the
     shipped SDL_VIDEODRIVER=fbcon.

Also make sure the timezone and NTP are right:
       sudo timedatectl set-timezone Europe/Amsterdam
       sudo timedatectl set-ntp true
EOF
