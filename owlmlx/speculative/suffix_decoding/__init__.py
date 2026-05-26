"""SuffixDecoding-style n-gram speculative decoding.

C0 phase: pure-Python algorithm with synthetic oracles. No model loading,
no mlx-lm dependency. See docs/architect/design/F-2-ngram-suffix-spec.md
for the C0/C1/C2 phased rollout and gate criteria.

Public surface (re-exports):

- ``NgramSuffixTree`` — ingest token histories, look up continuations
- ``NgramProposer`` — turn lookups into a linear speculation chain
- ``SpeculationNode`` — node in the speculation tree
- ``verify_speculation`` — walk a speculation against an oracle, decide
  what's accepted
- ``VerifyResult`` — result shape (accepted tokens + acceptance counts)
"""

from owlmlx.speculative.suffix_decoding.proposer import (
    NgramProposer,
    SpeculationNode,
)
from owlmlx.speculative.suffix_decoding.suffix_tree import NgramSuffixTree
from owlmlx.speculative.suffix_decoding.verifier import (
    Oracle,
    VerifyResult,
    mlx_lm_batch_verify,
    verify_speculation,
)

__all__ = [
    "NgramSuffixTree",
    "NgramProposer",
    "SpeculationNode",
    "Oracle",
    "VerifyResult",
    "verify_speculation",
    "mlx_lm_batch_verify",
]
