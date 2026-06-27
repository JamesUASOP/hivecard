#!/bin/bash
# Install passwordless sudo for HiveCard hotspot SSID changes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SET_SSID_DEST="/usr/local/sbin/hivecard-set-wifi-ssid.sh"
SUDOERS_DEST="/etc/sudoers.d/hivecard-hotspot"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run as root: sudo $0" >&2
  exit 1
fi

install -m 755 "${SCRIPT_DIR}/hivecard-set-wifi-ssid.sh" "${SET_SSID_DEST}"
install -m 440 "${SCRIPT_DIR}/hivecard-hotspot.sudoers" "${SUDOERS_DEST}"
visudo -cf "${SUDOERS_DEST}"

echo "HiveCard hotspot controls installed."
