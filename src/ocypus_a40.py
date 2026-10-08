#!/usr/bin/env python3
"""Iota A40 temperature display, based on moyunkz's MIT driver and PR #3."""

import argparse
import math
import os
import signal
import sys
import time

VERSION = "1.0.0"
VID, PID, INTERFACE = 0x1A2C, 0x434D, 1


def dependencies():
    try:
        import hid
        import psutil
    except ImportError as error:
        raise RuntimeError(
            "Missing dependency. Install python3-hid and python3-psutil with apt."
        ) from error
    if not hasattr(hid, "device"):
        raise RuntimeError("Wrong hid module: use Ubuntu/Debian's python3-hid package.")
    return hid, psutil


def choose_sensor(sensors, name="auto", label="auto"):
    """Never silently substitute a motherboard, GPU or SSD sensor for the CPU."""
    names = [name] if name != "auto" else ["k10temp", "coretemp"]
    for group_name in names:
        entries = sensors.get(group_name, [])
        if label != "auto":
            entries = [entry for entry in entries if entry.label == label]
        elif group_name == "k10temp":
            entries = sorted(entries, key=lambda item: (
                {"Tdie": 0, "Tctl": 1}.get(item.label, 2), item.label
            ))
        elif group_name == "coretemp":
            entries = sorted(entries, key=lambda item: (
                not item.label.startswith("Package id"), item.label
            ))
        for entry in entries:
            value = float(entry.current)
            if math.isfinite(value) and 0 <= value <= 150:
                return group_name, entry.label, value
    raise RuntimeError(
        f"CPU sensor not found (sensor={name}, label={label}). "
        "Run 'ocypus-a40 sensors'; use --sensor and --label if needed."
    )


def build_report(temperature, unit="c", hidraw=False):
    """The verified libusb payload is 00 07 FF FF <unit> <tens> <ones> ... ."""
    if unit not in ("c", "f") or not math.isfinite(temperature):
        raise ValueError("Invalid temperature or unit")
    displayed = temperature if unit == "c" else temperature * 9 / 5 + 32
    number = max(0, min(99, int(round(displayed))))
    report = bytearray(65)
    report[1:4] = bytes([7, 255, 255])
    report[4] = int(unit == "f")
    report[5], report[6] = divmod(number, 10)
    # libusb discards the leading zero; hidraw expects the numbered report ID.
    return bytes(report[1:] if hidraw else report)


class Controller:
    def __init__(self, hid):
        self.hid = hid
        self.device = None
        self.hidraw = False

    def open(self):
        candidates = [item for item in self.hid.enumerate(VID, PID)
                      if item.get("interface_number") == INTERFACE]
        if len(candidates) != 1:
            raise RuntimeError(
                f"Expected one Iota A40 display interface; found {len(candidates)}. "
                "Check its internal USB cable. Multiple coolers are not supported."
            )
        path = candidates[0]["path"]
        if isinstance(path, str):
            path = path.encode()
        self.hidraw = path.startswith(b"/dev/hidraw")
        self.device = self.hid.device()
        try:
            self.device.open_path(path)
        except Exception:
            self.close()
            raise
        print(f"Connected to Iota A40 interface 1 ({path.decode(errors='replace')})", flush=True)

    def send(self, temperature, unit):
        report = build_report(temperature, unit, self.hidraw)
        written = self.device.write(report)
        if written != len(report):
            raise RuntimeError(f"Incomplete LCD write: {written}/{len(report)} bytes")

    def close(self):
        if self.device is not None:
            try:
                self.device.close()
            finally:
                self.device = None


def refresh_rate(value):
    value = float(value)
    if not math.isfinite(value) or not 0.2 <= value <= 60:
        raise argparse.ArgumentTypeError("Refresh rate must be between 0.2 and 60 seconds")
    return value


def run(args, hid, psutil):
    # Read the CPU before opening USB; a missing sensor must never display zero.
    choose_sensor(psutil.sensors_temperatures(), args.sensor, args.label)
    controller = Controller(hid)
    stopped = False

    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    last_log = None
    try:
        controller.open()
        while not stopped:
            name, label, temperature = choose_sensor(
                psutil.sensors_temperatures(), args.sensor, args.label
            )
            controller.send(temperature, args.unit)
            now = time.monotonic()
            if last_log is None or now - last_log >= 60:
                print(f"CPU {name}/{label}: {temperature:.1f} °C; LCD unit={args.unit.upper()}", flush=True)
                last_log = now
            time.sleep(args.rate)
    finally:
        controller.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ocypus Iota A40 CPU temperature display")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("sensors", help="List temperature sensor names and labels")
    sub.add_parser("diagnose", help="Check USB detection, CPU sensors and dependencies")
    on = sub.add_parser("on", help="Continuously display CPU temperature")
    on.add_argument("-s", "--sensor", default=os.getenv("OCYPUS_SENSOR", "auto"))
    on.add_argument("-l", "--label", default=os.getenv("OCYPUS_LABEL", "auto"))
    on.add_argument("-u", "--unit", choices=["c", "f"], default=os.getenv("OCYPUS_UNIT", "c"))
    on.add_argument("-r", "--rate", type=refresh_rate, default=os.getenv("OCYPUS_RATE", "1"))
    args = parser.parse_args(argv)
    if args.command == "on" and args.unit not in ("c", "f"):
        parser.error("OCYPUS_UNIT must be c or f")
    try:
        hid, psutil = dependencies()
        if args.command == "sensors":
            for name, entries in psutil.sensors_temperatures().items():
                for entry in entries:
                    print(f"{name}\t{entry.label or '<unlabelled>'}\t{entry.current:.1f} °C")
        elif args.command == "diagnose":
            devices = [d for d in hid.enumerate(VID, PID)
                       if d.get("interface_number") == INTERFACE]
            print(f"Version: {VERSION}; USB 1a2c:434d display interfaces: {len(devices)}")
            name, label, temperature = choose_sensor(psutil.sensors_temperatures())
            print(f"CPU sensor: {name}/{label} = {temperature:.1f} °C")
            if len(devices) != 1:
                raise RuntimeError("Check the cooler's internal USB cable; expected one display.")
            print("Detection OK. See 'systemctl status ocypus-a40' for service state.")
        else:
            run(args, hid, psutil)
    except (RuntimeError, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
