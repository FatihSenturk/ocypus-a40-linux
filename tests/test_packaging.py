"""Exercise package service lifecycle with isolated paths and stubbed system tools."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "commands"
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
                        TEST_LOG=str(self.log), SERVICE_ENABLED="yes")
        for relative in ["run/udev", "run/systemd/system", "etc/systemd/system"]:
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        for command in ["systemctl", "udevadm", "getent", "id", "addgroup", "adduser"]:
            path = self.bin / command
            path.write_text('''#!/bin/sh
printf '%s %s\\n' "$(basename "$0")" "$*" >> "$TEST_LOG"
if [ "$(basename "$0")" = systemctl ] && [ "$1" = is-enabled ]; then
    [ "$SERVICE_ENABLED" = yes ]
else
    exit 0
fi
''')
            path.chmod(0o755)

    def run_script(self, script, *args):
        text = (PROJECT / "packaging" / script).read_text()
        # Redirect every absolute path used by maintainer scripts into the sandbox.
        for prefix in ["/etc/systemd/system", "/var/lib/ocypus-a40", "/run/udev", "/run/systemd/system"]:
            text = text.replace(prefix, str(self.root / prefix.lstrip("/")))
        subprocess.run(["sh", "-c", text, script, *args], env=self.env,
                       check=True, capture_output=True, text=True)
        return self.log.read_text()

    def test_new_install_enables_service(self):
        log = self.run_script("postinst", "configure")
        self.assertIn("systemctl enable --now ocypus-a40.service", log)
        self.assertIn("udevadm control --reload-rules", log)

    def test_disabled_service_stays_disabled_on_upgrade(self):
        self.env["SERVICE_ENABLED"] = "no"
        log = self.run_script("postinst", "configure", "0.9.0")
        self.assertNotIn("systemctl enable", log)
        self.assertNotIn("systemctl restart", log)

    def test_known_manual_install_is_migrated_and_preserved(self):
        legacy = self.root / "etc/systemd/system/ocypus-a40.service"
        contents = "ExecStart=/usr/bin/python3 -u /opt/ocypus-a40/ocypus-control.py on -s k10temp\n"
        legacy.write_text(contents)
        log = self.run_script("postinst", "configure")
        backup = self.root / "var/lib/ocypus-a40/legacy/ocypus-a40.service"
        self.assertEqual(backup.read_text(), contents)
        self.assertFalse(legacy.exists())
        self.assertLess(log.index("systemctl disable --now"), log.index("systemctl enable --now"))

    def test_unrelated_administrator_unit_is_preserved(self):
        legacy = self.root / "etc/systemd/system/ocypus-a40.service"
        legacy.write_text("ExecStart=/custom/program\n")
        self.run_script("postinst", "configure")
        self.assertEqual(legacy.read_text(), "ExecStart=/custom/program\n")

    def test_remove_stops_service_and_reloads_udev(self):
        log = self.run_script("prerm", "remove")
        self.assertIn("systemctl stop ocypus-a40.service", log)
        log = self.run_script("postrm", "remove")
        self.assertIn("systemctl disable ocypus-a40.service", log)
        self.assertIn("udevadm control --reload-rules", log)


if __name__ == "__main__":
    unittest.main()
