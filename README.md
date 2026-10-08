# Ocypus Iota A40 — Linux temperature display

Show your CPU temperature on the Iota A40's built-in display with one install command.
Runs automatically at boot, chooses an AMD or Intel CPU sensor, and needs no desktop app.

[Türkçe kullanım](docs/README.tr.md) · [Download the .deb package](https://github.com/FatihSenturk/ocypus-a40-linux/releases/latest)

## Install

On **Ubuntu/Debian with systemd**, paste this into a terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/FatihSenturk/ocypus-a40-linux/v1.0.0/install.sh | bash
```

The installer downloads the tagged source, builds a small Debian package and uses
`apt` to install it and its dependencies. Enter your sudo password when prompted.
It starts the display service and enables it at boot. If curl is missing, install
it with `sudo apt install curl` first.

Prefer a downloaded package? Get `ocypus-a40_1.0.0_all.deb` from
[Releases](https://github.com/FatihSenturk/ocypus-a40-linux/releases/latest), then run
this command in the folder where you downloaded it:

```bash
sudo apt install ./ocypus-a40_1.0.0_all.deb
```

You can also open the `.deb` in a graphical package installer that resolves
dependencies. Desktop support for local package files varies; the apt command
above is the supported fallback.

## Compatibility

| Component | Support |
| --- | --- |
| Cooler | Ocypus Iota A40, USB ID `1a2c:434d`, interface 1 |
| Verified hardware | Ubuntu 24.04 LTS, AMD CPU, physical Iota A40 display |
| Debian and Intel CPUs | Implemented and covered by automated checks; hardware confirmation welcome |
| Other Ocypus models / multiple coolers | Not supported by this release |
| Other Linux distributions | Not packaged by this release |

Connect the cooler's display cable to the motherboard's internal USB 2.0 header.
The fan connection alone does not connect the display. Temperature is refreshed
every second; the driver restarts after USB or sensor errors.

The protocol correction used here has been verified on an Iota A40 in the
upstream project and in the initial Ubuntu setup behind this project. The new
package's install/remove lifecycle is checked in a sandbox; installing this exact
release on more hardware remains useful validation.

## Check and configure

```bash
ocypus-a40 diagnose
ocypus-a40 sensors
systemctl status ocypus-a40 --no-pager
sudo journalctl -u ocypus-a40 -n 30 --no-pager
```

Settings live in `/etc/default/ocypus-a40`. Defaults select the CPU sensor and
use Celsius. On AMD, `Tdie` is preferred, then `Tctl`; on Intel, a CPU package
sensor is preferred. The driver never substitutes an SSD or GPU sensor.

Example settings:

```ini
OCYPUS_SENSOR=auto
OCYPUS_LABEL=auto
OCYPUS_UNIT=c
OCYPUS_RATE=1
```

To select a specific sensor, use the names printed by `ocypus-a40 sensors`, for
example `OCYPUS_SENSOR=k10temp` and `OCYPUS_LABEL=Tctl`. Put quotes around labels
with spaces, such as `OCYPUS_LABEL="Package id 0"`. Restart after editing:

```bash
sudo systemctl restart ocypus-a40
```

The display accepts two digits. Readings above 99 in the selected unit are
capped at 99, so Celsius is recommended. Fahrenheit is implemented but has not
been checked on physical hardware.

## Remove

```bash
sudo apt remove ocypus-a40
```

This stops the service and removes package-owned program files and USB rules.
Use `sudo apt purge ocypus-a40` to remove the configuration too. Dependencies and
the reserved `ocypus-a40` system account are retained.

## Blank display?

1. Run `ocypus-a40 diagnose` to check the device and CPU sensor.
2. Look at the service journal above. After suspend, try restarting the service.
3. Check the internal USB cable with the PC powered off.
4. Stop any other program controlling the same display. Before a foreground
   test, run `sudo systemctl stop ocypus-a40`, then `sudo ocypus-a40 on`.
   Stop with Ctrl+C and restore the service with `sudo systemctl start ocypus-a40`.

The USB device is labelled “USB Gaming Keyboard” by its controller firmware;
that name is expected. “Active (running)” confirms the process, not the physical
display: check the cooler itself.

Migrating from the first manual `kur.sh` setup automatically replaces that known
legacy service and preserves its unit in `/var/lib/ocypus-a40/legacy/`. The old
`/opt/ocypus-a40` files and administrator-created USB rules are left in place.

## Build and test

```bash
python3 -m unittest discover -s tests -v
bash build-deb.sh
```

The package appears in `dist/`. No hardware, root access, or third-party Python
packages are needed for the unit tests. CI also builds and inspects the package.

## Credits and license

MIT. Based on [moyunkz's Linux driver](https://github.com/moyunkz/ocypus-a40-digital-linux)
and [roubilibo's Iota A40 output-report fix](https://github.com/moyunkz/ocypus-a40-digital-linux/pull/3).
See [NOTICE.md](NOTICE.md) for attribution. This is an independent community project.
