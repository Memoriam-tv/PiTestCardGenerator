# piclock

Fullscreen broadcast clock for a Raspberry Pi 2 on HDMI, no desktop:

* PM5544-style test card (17 x 13 grid, castellated border, greyscale staircase,
  75 % EBU colour bars, definition gratings, centre circle) drawn procedurally at
  the native resolution;
* round analog clock — 60 tick marks, 12 major marks, hour/minute/second hands —
  centred on the card circle, second hand sweeping once per rendered frame;
* time-of-day timecode `HH:MM:SS:FF` in the ident bar below the dial, where `FF`
  advances every rendered frame at **the actual HDMI output rate**, detected at
  startup — nothing is hardcoded to 25 or 30.

Everything static is rendered once into one background surface; each frame only
the hand bounding boxes and the timecode digits are repainted, so a 900 MHz
Cortex-A7 keeps up at 1080p.

## Run

```bash
python3 -m piclock                              # on the Pi: fullscreen at the current HDMI mode
.venv/bin/python -m piclock --windowed --size 1280x720   # dev mode on a workstation
```

| flag | default | meaning |
|---|---|---|
| `--fps N` | auto | override the detected HDMI rate |
| `--size WxH` | native | force resolution (mode request or window size) |
| `--windowed` | off | run in a window instead of fullscreen |
| `--frames N` | off | exit after N frames |
| `--dump-frames DIR` | off | save every frame as `frame_%04d.png` |
| `--log-tc` | off | print the timecode of every frame |
| `--stats` | off | print frame-time stats once a second |

`Esc`, `q`, `SIGINT` and `SIGTERM` all stop the loop cleanly (exit code 0).

## Dev machine setup

pygame comes from apt on the Pi, so `python3 -m piclock` is the right command
there. On a workstation it is installed into a venv instead:

```bash
python3.11 -m venv .venv
.venv/bin/pip install "pygame>=2.5,<3"
.venv/bin/python -m piclock --windowed --size 1280x720
```

**This repo deliberately carries no `.tool-versions`.** If a version manager
(asdf, mise, pyenv) owns `python3`, a bare `python3 -m piclock` in this
directory fails before it reaches the code:

```
No version is set for command python3
Consider adding one of the following versions in your config file at .../.tool-versions
```

Pinning an interpreter there would not help: the shimmed interpreter is not the
one holding pygame, so it would trade that message for `ModuleNotFoundError:
No module named 'pygame'`. Call the venv interpreter by path — `.venv/bin/python`
— or `source .venv/bin/activate` first, which puts it ahead of the shim on
`PATH`. The systemd unit sidesteps the same class of problem by invoking
`/usr/bin/python3` absolutely.

## Install on the Pi

Dependencies come from apt — pygame is never built from source on a Pi 2:

```bash
sudo apt-get install -y python3-pygame fonts-dejavu-core libegl1 libgles2 libgbm1
```

Then, from a checkout of this repo on the Pi:

```bash
sudo bash deploy/install.sh
```

That copies the package to `/opt/piclock`, installs
`/etc/systemd/system/piclock.service` (runs as `pi` on tty1 with
`SDL_VIDEODRIVER=kmsdrm`) and starts it. Check with `systemctl status piclock`.

### Three manual system tweaks

1. **Boot to console, no desktop:** `sudo raspi-config nonint do_boot_behaviour B1`
2. **KMS driver:** `/boot/firmware/config.txt` must contain `dtoverlay=vc4-kms-v3d`
   (the Bookworm default). If SDL cannot open a DRM device, try
   `dtoverlay=vc4-fkms-v3d`.
3. **No console blanking:** append `consoleblank=0` to `/boot/firmware/cmdline.txt`
   (one line, space separated), so DPMS never blanks the HDMI output.

Also set the clock source, because both the dial and the timecode are local time
on a board without an RTC:

```bash
sudo timedatectl set-timezone Europe/Amsterdam
sudo timedatectl set-ntp true
```

## Notes

* Tested against pygame 2 / SDL 2. Only APIs present in the Bookworm apt package
  (pygame 2.1.2) are used; `pygame.display.get_current_refresh_rate` is probed
  with `getattr` and simply absent there.
* Rate detection order: `--fps`, then the pygame-ce refresh-rate API if present,
  then a 40-flip measurement snapped to the nearest standard rate (KMSDRM
  page-flips are vblank-synced, so this measures the real HDMI mode), then 25.
* If `max frame ms` reported by `--stats` exceeds the frame budget at 1080p, add
  `--size 1280x720` to `ExecStart` in the unit. Do not reintroduce full-screen
  repaints or `pygame.transform.rotate`.
