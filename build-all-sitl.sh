#!/bin/bash
set -euo pipefail
cd ~/ardupilot
source ~/venv-ardupilot/bin/activate
mkdir -p ~/.hivecard/logs

TARGETS=(sub blimp antennatracker heli AP_Periph)
for t in "${TARGETS[@]}"; do
  log=~/.hivecard/logs/build-${t}.log
  echo "=== $(date -Iseconds) starting waf ${t} ===" | tee "$log"
  if ./waf "$t" -j4 >>"$log" 2>&1; then
    echo "=== $(date -Iseconds) ${t} finished successfully ===" | tee -a "$log"
  else
    echo "=== $(date -Iseconds) ${t} FAILED (exit $?) ===" | tee -a "$log"
  fi
done

echo "=== $(date -Iseconds) all builds done ===" >> ~/.hivecard/logs/build-all.log
ls -la ~/ardupilot/build/sitl/bin/ >> ~/.hivecard/logs/build-all.log
