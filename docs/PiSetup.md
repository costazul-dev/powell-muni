# Raspberry Pi Setup

Runs `main.py` on a Raspberry Pi as a systemd service driving the 128x64
HUB75 panel through the `rgbmatrix` hardware backend.

`main.py` runs as one long-lived process rather than from a systemd timer: the
matrix library refreshes the panel from a background thread, and the panel goes
dark when the process exits.

## Hardware Constraints

- **No Raspberry Pi 5.** [hzeller/rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix)
  does not support it. Supported targets include the Pi 4, Pi 3B+, and Pi Zero 2 W.
- **Dedicated 5V/4A supply.** The [Adafruit 6484](https://www.adafruit.com/product/6484)
  panel can draw up to 4A at 5V. Power it from its own supply, not from the Pi.
- **`E` address line required.** The panel is 1/32 scan and uses 5 address
  lines. The Adafruit RGB Matrix Bonnet and HAT need a jumper soldered to
  enable `E`; see the
  [Adafruit RGB Matrix Bonnet guide](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi)
  or the [Adafruit RGB Matrix HAT guide](https://learn.adafruit.com/adafruit-rgb-matrix-plus-real-time-clock-hat-for-raspberry-pi)
  for the jumper that matches your board.

## Install the App

Clone into `/opt/powell-muni` and create a virtualenv with access to system
site packages, so it can see the `rgbmatrix` bindings installed in the next
step:

```bash
sudo git clone https://github.com/costazul-dev/powell-muni.git /opt/powell-muni
cd /opt/powell-muni
sudo python3 -m venv --system-site-packages .venv
sudo .venv/bin/pip install -r requirements.txt
```

Install `requirements.txt` only. `requirements-dev.txt` adds `RGBMatrixEmulator`
and test tools that are not needed on the Pi.

## Build the `rgbmatrix` Bindings

The `rgbmatrix` Python module is built from source and is not in
`requirements.txt`. Follow the upstream
[`bindings/python/README.md`](https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/bindings/python/README.md)
to build and install it with the Pi's system `python3`, so the
`--system-site-packages` virtualenv picks it up.

Check that it imports from the virtualenv:

```bash
/opt/powell-muni/.venv/bin/python -c "import rgbmatrix"
```

## Disable Onboard Audio

Onboard audio conflicts with the matrix timing. In `/boot/firmware/config.txt`
(`/boot/config.txt` on older Raspberry Pi OS releases), set:

```
dtparam=audio=off
```

Reboot after the change.

## Configure

```bash
cd /opt/powell-muni
sudo cp config.yaml.example config.yaml
sudo cp .env.example .env              # set API_511_KEY
```

In `config.yaml`:

- Set `display.backend: hardware`.
- Set the real `stop_code` for each row.
- Tune `display.hardware.gpio_slowdown` for the Pi model. Faster boards need a
  higher value; raise it if the panel flickers or shows garbage, lower it if the
  refresh rate is too low. Upstream's README lists starting values per model.

Run once in the foreground to check the panel before installing the service:

```bash
sudo .venv/bin/python main.py --config /opt/powell-muni/config.yaml
```

`rgbmatrix` needs root to access GPIO and drops privileges after
initialization, so the app and the service run as root.

## Install the systemd Service

```bash
sudo cp /opt/powell-muni/deploy/powell-muni.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now powell-muni
```

View logs:

```bash
journalctl -u powell-muni -f
```

The unit restarts the app 10 seconds after any exit. After pulling new code,
apply it with `sudo systemctl restart powell-muni`.
