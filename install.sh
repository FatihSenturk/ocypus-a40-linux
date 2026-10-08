#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  --help|-h)
    echo 'Ocypus Iota A40 installer for Ubuntu/Debian with systemd.'
    echo 'Usage: bash install.sh [--build-only]'
    echo 'Removal: sudo apt remove ocypus-a40'
    exit 0 ;;
  ''|--build-only) ;;
  *) echo "Unknown option: $1" >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo 'Too many arguments' >&2; exit 2; }
for command in dpkg-deb python3; do
  command -v "$command" >/dev/null || { echo "Missing $command; Ubuntu/Debian is required." >&2; exit 1; }
done
if [[ "${1:-}" != --build-only ]]; then
  command -v apt-get >/dev/null || { echo 'apt-get is required.' >&2; exit 1; }
  [[ -d /run/systemd/system ]] || { echo 'A running systemd system is required.' >&2; exit 1; }
fi
source_path=${BASH_SOURCE[0]:-}
source_dir=''
if [[ -n "$source_path" && -f "$source_path" ]]; then
  source_dir=$(cd -- "$(dirname -- "$source_path")" && pwd)
fi
if [[ -z "$source_dir" || ! -f "$source_dir/src/ocypus_a40.py" ]]; then
  command -v curl >/dev/null || { echo 'Install curl first: sudo apt install curl' >&2; exit 1; }
  temporary=$(mktemp -d)
  trap 'rm -rf -- "$temporary"' EXIT
  echo 'Downloading Ocypus Iota A40 Linux v1.0.0...'
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    --connect-timeout 10 --max-time 90 \
    https://codeload.github.com/FatihSenturk/ocypus-a40-linux/tar.gz/refs/tags/v1.0.0 \
    -o "$temporary/source.tar.gz"
  tar -xzf "$temporary/source.tar.gz" -C "$temporary"
  if [[ "${1:-}" == --build-only ]]; then
    bash "$temporary/ocypus-a40-linux-1.0.0/build-deb.sh" "$PWD/dist"
  else
    bash "$temporary/ocypus-a40-linux-1.0.0/install.sh" "$@"
  fi
  exit $?
fi
if [[ "${1:-}" == --build-only ]]; then
  bash "$source_dir/build-deb.sh"
  exit 0
fi
echo 'Building the package...'
package_dir=$(mktemp -d)
chmod 0755 "$package_dir"
trap 'rm -rf -- "$package_dir"' EXIT
bash "$source_dir/build-deb.sh" "$package_dir"
chmod 0644 "$package_dir/ocypus-a40_1.0.0_all.deb"
if [[ $EUID -eq 0 ]]; then
  apt-get update
  apt-get install -y "$package_dir/ocypus-a40_1.0.0_all.deb"
else
  sudo apt-get update
  sudo apt-get install -y "$package_dir/ocypus-a40_1.0.0_all.deb"
fi
echo
echo 'Package installed. Check the physical display.'
echo 'Diagnostics: ocypus-a40 diagnose'
echo 'Service: systemctl status ocypus-a40 --no-pager'
echo 'Removal: sudo apt remove ocypus-a40'
