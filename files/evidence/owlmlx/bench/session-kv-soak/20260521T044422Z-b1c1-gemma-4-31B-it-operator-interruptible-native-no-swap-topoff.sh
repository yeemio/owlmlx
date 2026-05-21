#!/usr/bin/env bash
set -uo pipefail

cd /Users/yeemio/AI/gitrep/owlmlx

LOG="files/evidence/owlmlx/bench/session-kv-soak/20260521T044422Z-b1c1-gemma-4-31B-it-operator-interruptible-native-no-swap-topoff.log"
EXIT="files/evidence/owlmlx/bench/session-kv-soak/20260521T044422Z-b1c1-gemma-4-31B-it-operator-interruptible-native-no-swap-topoff.exit"

caffeinate -dimsu uv run python scripts/bench/eviction_soak.py \
  --gate b1c1-no-swap-soak \
  --backend native \
  --model /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --model-label gemma-4-31B-it \
  --model-gb 60 \
  --duration-s 7200 \
  --required-duration-s 86400 \
  --sample-interval-s 60 \
  --warmup-cycles 1 \
  --session-cache-ttl-s 90000 \
  --max-tokens 2 \
  --rehearsal-group-id b1c1-current-mac-operator-interruptible \
  --rehearsal-segment-id 20260521T044422Z-b1c1-current-mac-topoff-segment \
  --resumes-prior-segment \
  --interruption-reason planned_stop \
  --output files/evidence/owlmlx/bench/session-kv-soak \
  >"${LOG}" 2>&1

code=$?
printf "%s\n" "${code}" >"${EXIT}"
printf "B1C1_TOPOFF_EXIT code=%s at %s\n" "${code}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"${LOG}"
exit "${code}"
