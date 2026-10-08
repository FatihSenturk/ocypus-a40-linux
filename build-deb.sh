#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
destination=${1:-"$root/dist"}
mkdir -p -- "$destination"
destination=$(cd -- "$destination" && pwd)
stage=$(mktemp -d)
chmod 0755 "$stage"
trap 'rm -rf -- "$stage"' EXIT
install -d "$stage/DEBIAN" "$stage/usr/lib/ocypus-a40" "$stage/usr/bin" \
  "$stage/usr/lib/systemd/system" "$stage/usr/lib/udev/rules.d" \
  "$stage/etc/default" "$stage/usr/share/doc/ocypus-a40"
install -m 0644 "$root/packaging/control" "$stage/DEBIAN/control"
for script in postinst prerm postrm; do
  install -m 0755 "$root/packaging/$script" "$stage/DEBIAN/$script"
done
echo /etc/default/ocypus-a40 > "$stage/DEBIAN/conffiles"
install -m 0644 "$root/src/ocypus_a40.py" "$stage/usr/lib/ocypus-a40/"
install -m 0644 "$root/packaging/ocypus-a40.service" "$stage/usr/lib/systemd/system/"
install -m 0644 "$root/packaging/99-ocypus-a40.rules" "$stage/usr/lib/udev/rules.d/"
install -m 0644 "$root/packaging/ocypus-a40.default" "$stage/etc/default/ocypus-a40"
install -m 0644 "$root/LICENSE" "$stage/usr/share/doc/ocypus-a40/copyright"
install -m 0644 "$root/NOTICE.md" "$stage/usr/share/doc/ocypus-a40/NOTICE.md"
cat > "$stage/usr/bin/ocypus-a40" <<'SH'
#!/bin/sh
exec /usr/bin/python3 /usr/lib/ocypus-a40/ocypus_a40.py "$@"
SH
chmod 0755 "$stage/usr/bin/ocypus-a40"
dpkg-deb --root-owner-group --build "$stage" "$destination/ocypus-a40_1.0.0_all.deb"
