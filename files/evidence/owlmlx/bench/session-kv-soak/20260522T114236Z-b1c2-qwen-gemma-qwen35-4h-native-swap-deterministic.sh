#!/usr/bin/env bash
set -o pipefail
cd /Users/yeemio/AI/gitrep/owlmlx
printf '%s\n' "$$" > "files/evidence/owlmlx/bench/session-kv-soak/20260522T114236Z-b1c2-qwen-gemma-qwen35-4h-native-swap-deterministic.pid"
uv run python scripts/bench/eviction_soak.py \
  --gate b1c2-soak-plus-swap \
  --runtime owlmlx \
  --backend native \
  --model-a /Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit \
  --model-a-gb 16 \
  --model /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --model-gb 60 \
  --model-b /Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit \
  --model-b-gb 20 \
  --duration-s 14400 \
  --required-duration-s 86400 \
  --swap-count 1 \
  --required-swap-count 6 \
  --sample-interval-s 60 \
  --max-tokens 1 \
  --profile-memory-gb 128 \
  --b1c1-prerequisite-satisfied
code=$?
printf '%s\n' "$code" > "files/evidence/owlmlx/bench/session-kv-soak/20260522T114236Z-b1c2-qwen-gemma-qwen35-4h-native-swap-deterministic.exit"
exit "$code"
