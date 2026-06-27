#!/bin/bash
# Install HiveCard hotspot captive portal (DNS + port 80 redirect).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DNSMASQ_DEST="/etc/NetworkManager/dnsmasq-shared.d/hivecard.conf"
REDIRECT_DEST="/usr/local/sbin/hivecard-captive-redirect.sh"
SERVICE_DEST="/etc/systemd/system/hivecard-captive-redirect.service"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run as root: sudo $0" >&2
  exit 1
fi

install -m 644 "${SCRIPT_DIR}/hivecard-dnsmasq.conf" "${DNSMASQ_DEST}"
install -m 755 "${SCRIPT_DIR}/hivecard-captive-redirect.sh" "${REDIRECT_DEST}"
install -m 644 "${SCRIPT_DIR}/hivecard-captive-redirect.service" "${SERVICE_DEST}"

systemctl daemon-reload
systemctl enable hivecard-captive-redirect.service
systemctl restart hivecard-captive-redirect.service

# Reload NetworkManager dnsmasq for the shared hotspot.
if nmcli -t -f NAME,TYPE connection show --active | grep -q ':802-11-wireless'; then
  HOTSPOT="$(nmcli -t -f NAME,TYPE connection show | awk -F: '$2=="802-11-wireless" && $1 ~ /[Hh]otspot|[Hh]ive[Cc]ard/ {print $1; exit}')"
  if [[ -n "${HOTSPOT:-}" ]]; then
    nmcli connection down "${HOTSPOT}" || true
    sleep 1
    nmcli connection up "${HOTSPOT}" || true
  fi
fi
systemctl reload NetworkManager 2>/dev/null || systemctl restart NetworkManager

echo "HiveCard captive portal installed."
echo "Hotspot login URL: http://hivecard/login"
echo "Alternate URL:     http://10.42.0.1/login"
