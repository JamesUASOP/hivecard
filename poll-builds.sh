#!/bin/bash
while pgrep -f 'python3 ./waf' >/dev/null 2>&1; do
  for t in sub blimp antennatracker sitl_periph_universal; do
    p=$(grep -oE '\[[0-9]+/[0-9]+\]' "$HOME/.hivecard/logs/build-${t}.log" 2>/dev/null | tail -1)
    if [ -n "$p" ]; then
      echo "${t}: ${p}"
    fi
  done
  ls "$HOME/ardupilot/build/sitl/bin/" 2>/dev/null | tr '\n' ' '
  echo
  sleep 60
done
echo "=== ALL BUILDS DONE ==="
ls -la "$HOME/ardupilot/build/sitl/bin/"
tail -5 "$HOME/.hivecard/logs/build-all-runner.log"
