#!/bin/zsh
cd /Users/yeemio/AI/gitrep/owlmlx || exit 97
echo B1C1_SEGMENT_STARTED stamp=20260520T075226Z at $(date -u +%Y-%m-%dT%H:%M:%SZ)
caffeinate -dimsu uv run python scripts/bench/eviction_soak.py \
  --gate b1c1-no-swap-soak \
  --backend native \
  --model "/Users/yeemio/AI/Agent/models/gemma-4-31B-it" \
  --model-label gemma-4-31B-it \
  --model-gb 60 \
  --duration-s 86400 \
  --required-duration-s 86400 \
  --sample-interval-s 60 \
  --warmup-cycles 1 \
  --session-cache-ttl-s 90000 \
  --max-tokens 2 \
  --rehearsal-group-id "b1c1-current-mac-operator-interruptible-20260520" \
  --rehearsal-segment-id "20260520T075226Z-b1c1-current-mac-segment" \
  --interruption-reason planned_stop \
  --output "files/evidence/owlmlx/bench/session-kv-soak"
rc=$?
echo $rc > "files/evidence/owlmlx/bench/session-kv-soak/20260520T075226Z-b1c1-gemma-4-31B-it-operator-interruptible-native-no-swap.exit"
echo B1C1_SEGMENT_EXIT code=$rc at $(date -u +%Y-%m-%dT%H:%M:%SZ)
exit $rc
