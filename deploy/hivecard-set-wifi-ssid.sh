#!/bin/bash
# Set the HiveCard hotspot SSID and re-activate the AP if it is running.
set -euo pipefail

SSID="${1:?SSID required}"
CONN="${2:-HiveCard-Hotspot}"

if [[ ${#SSID} -lt 1 || ${#SSID} -gt 32 ]]; then
  echo "SSID length must be 1-32 characters" >&2
  exit 1
fi

nmcli connection modify "${CONN}" 802-11-wireless.ssid "${SSID}"

if nmcli -t -f NAME connection show --active | grep -qx "${CONN}"; then
  nmcli connection down "${CONN}" || true
  sleep 1
  nmcli connection up "${CONN}"
fi

echo "Hotspot SSID set to: ${SSID}"
