#!/usr/bin/env zsh
set -u
cd /Users/yeemio/AI/gitrep/owlmlx
export OWLMLX_SESSION_CACHE_ENABLED=1
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
  --rotation-label qwen-gemma-qwen35-prompt-reset-3000-4h \
  --duration-s 14400 \
  --required-duration-s 86400 \
  --swap-count 1 \
  --required-swap-count 6 \
  --sample-interval-s 60 \
  --max-tokens 1 \
  --profile-memory-gb 128 \
  --b1c1-prerequisite-satisfied \
  --b1c2-prompt-growth-max-chars 3000 \
  --session-id-prefix b1c2-prompt-reset-swap-3000
code=$?
printf "%s\n" "$code" > /Users/yeemio/AI/gitrep/owlmlx/files/evidence/owlmlx/bench/session-kv-soak/20260525T061019Z-b1c2-qwen-gemma-qwen35-prompt-reset-3000-4h-native-swap.exit
exit "$code"
