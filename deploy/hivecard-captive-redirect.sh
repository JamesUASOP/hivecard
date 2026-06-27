#!/bin/bash
# Redirect HTTP port 80 on the hotspot interface to hivecard-web (8080) via nftables.
set -euo pipefail

IFACE="${HIVECARD_HOTSPOT_IFACE:-wlan0}"
TO_PORT="${HIVECARD_WEB_PORT:-8080}"
NFT="${NFT:-nft}"

if ! command -v "${NFT}" >/dev/null 2>&1; then
  echo "nftables not found; install with: sudo apt install nftables" >&2
  exit 1
fi

if ! "${NFT}" list table ip hivecard >/dev/null 2>&1; then
  "${NFT}" add table ip hivecard
fi

if ! "${NFT}" list chain ip hivecard prerouting >/dev/null 2>&1; then
  "${NFT}" add chain ip hivecard prerouting '{ type nat hook prerouting priority dstnat; policy accept; }'
fi

if "${NFT}" list chain ip hivecard prerouting | grep -q "redirect to :${TO_PORT}"; then
  exit 0
fi

"${NFT}" add rule ip hivecard prerouting iifname "${IFACE}" tcp dport 80 redirect to ":${TO_PORT}"
