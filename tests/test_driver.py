import importlib.util
import math
import sys
import unittest
from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location(
    "driver", Path(__file__).resolve().parents[1] / "src/ocypus_a40.py"
)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
Sensor = namedtuple("Sensor", "label current")


class SensorTests(unittest.TestCase):
    def test_amd_cpu_wins_over_gpu_and_disk(self):
        sensors = {"amdgpu": [Sensor("edge", 90)], "nvme": [Sensor("Composite", 40)],
                   "k10temp": [Sensor("Tccd1", 49), Sensor("Tctl", 55), Sensor("Tdie", 53)]}
        self.assertEqual(driver.choose_sensor(sensors), ("k10temp", "Tdie", 53))

    def test_intel_uses_package_before_core(self):
        sensors = {"coretemp": [Sensor("Core 0", 30), Sensor("Package id 0", 44)]}
        self.assertEqual(driver.choose_sensor(sensors), ("coretemp", "Package id 0", 44))

    def test_missing_cpu_does_not_fall_back_to_gpu(self):
        with self.assertRaises(RuntimeError):
            driver.choose_sensor({"amdgpu": [Sensor("edge", 60)]})

    def test_invalid_values_do_not_become_zero(self):
        for value in [math.nan, math.inf, -1, 151]:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                driver.choose_sensor({"k10temp": [Sensor("Tctl", value)]})

    def test_explicit_label_and_missing_label(self):
        sensors = {"k10temp": [Sensor("Tctl", 55), Sensor("Tccd1", 51)]}
        self.assertEqual(driver.choose_sensor(sensors, "k10temp", "Tccd1")[2], 51)
        with self.assertRaises(RuntimeError):
            driver.choose_sensor(sensors, "k10temp", "Tdie")


class ProtocolTests(unittest.TestCase):
    def test_upstream_verified_57_degree_packet(self):
        packet = driver.build_report(57.4)
        self.assertEqual(packet, bytes([0, 7, 255, 255, 0, 5, 7]) + bytes(58))

    def test_backend_framing_preserves_wire_payload(self):
        libusb = driver.build_report(57, hidraw=False)
        hidraw = driver.build_report(57, hidraw=True)
        self.assertEqual(hidraw, libusb[1:])
        self.assertEqual(len(hidraw), 64)

    def test_fahrenheit_flag_and_display_limit(self):
        self.assertEqual(driver.build_report(20, "f")[4:7], bytes([1, 6, 8]))
        self.assertEqual(driver.build_report(99, "f")[5:7], bytes([9, 9]))
        self.assertEqual(driver.build_report(100, "c")[5:7], bytes([9, 9]))

    def test_non_finite_reading_not_sent(self):
        with self.assertRaises(ValueError):
            driver.build_report(math.nan)


class FakeDevice:
    def __init__(self, written=65):
        self.written = written
        self.path = None
        self.closed = False

    def open_path(self, path):
        self.path = path

    def write(self, data):
        return self.written

    def close(self):
        self.closed = True


class ControllerTests(unittest.TestCase):
    def test_chooses_display_not_keyboard_interface(self):
        device = FakeDevice()
        hid = SimpleNamespace(enumerate=lambda *_: [
            {"interface_number": 0, "path": b"keyboard"},
            {"interface_number": 1, "path": b"1-9:1.1"}], device=lambda: device)
        controller = driver.Controller(hid)
        controller.open()
        self.assertEqual(device.path, b"1-9:1.1")
        controller.send(57, "c")
        controller.close()
        self.assertTrue(device.closed)

    def test_short_write_triggers_reconnect(self):
        controller = driver.Controller(None)
        controller.device = FakeDevice(written=3)
        with self.assertRaises(RuntimeError):
            controller.send(57, "c")

    def test_ambiguous_devices_not_opened(self):
        hid = SimpleNamespace(enumerate=lambda *_: [
            {"interface_number": 1, "path": b"one"},
            {"interface_number": 1, "path": b"two"}])
        with self.assertRaises(RuntimeError):
            driver.Controller(hid).open()


class ConfigurationTests(unittest.TestCase):
    def test_rejects_busy_loop_and_nonfinite_refresh(self):
        for value in ["0", "-1", "nan", "inf", "61"]:
            with self.subTest(value=value), self.assertRaises(Exception):
                driver.refresh_rate(value)

    def test_version_needs_no_hardware_or_dependencies(self):
        with self.assertRaises(SystemExit) as result:
            driver.main(["--version"])
        self.assertEqual(result.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
