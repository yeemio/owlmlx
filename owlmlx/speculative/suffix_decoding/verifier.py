"""Accept/reject a speculation chain against an oracle.

The oracle abstraction (``Oracle = Callable[[list[int]], int]``) lets C0
substitute a synthetic next-token function so the algorithm can be tested
without loading a model. C1 replaces the oracle with a real mlx-lm batch
verify primitive (one model forward pass that yields a token per position).

For C0 we only verify **linear chains** (one branch per level). When the
proposer is extended to tree-shaped speculation, this verifier must grow a
branch-following step; the public ``verify_speculation`` signature is
forward-compatible (callers receive the same ``VerifyResult`` shape).

Algorithm (linear chain):

1. Walk down the chain. At each level, ask the oracle for the true next
   token given the running context (initial context + accepted tokens).
2. If the oracle agrees with the chain's token, accept and descend.
3. If the oracle disagrees, accept the oracle's token as the "bonus"
   (the +1 token we always get from a single model forward), stop, and
   return.
4. If the chain runs out with everything accepted, ask the oracle once
   more for the token after the chain — that is also a bonus we get for
   free from the same forward pass. Both branches return at least one
   token in ``accepted_tokens``.

This file imports nothing model-related.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from owlmlx.speculative.suffix_decoding.proposer import SpeculationNode


Oracle = Callable[[list[int]], int]
"""A function that returns the true next token given the current context.

In C0 tests, this is a synthetic deterministic function. In C1 it wraps a
real mlx-lm model: caller batches ``context + speculation_chain`` into one
forward pass and exposes per-position argmax as ``oracle(prefix)`` lookups.
"""


@dataclass
class VerifyResult:
    """Outcome of one verify-speculation call.

    Attributes:
        accepted_tokens: tokens to commit to the output stream. Always
            length >= 1 (we always get at least the bonus token from the
            forward pass). The last entry is the bonus that the oracle
            provided for the position immediately after the last accepted
            speculation token.
        chain_accept_count: how many tokens from the speculation chain
            were accepted (0..chain_length). 0 means the first speculation
            token did not match the oracle; ``chain_length`` means full
            speculation was accepted.
        chain_length: length of the original speculation chain (0 when no
            speculation was proposed).
    """

    accepted_tokens: list[int]
    chain_accept_count: int
    chain_length: int

    @property
    def acceptance_rate(self) -> float:
        """Fraction of speculation tokens accepted, in ``[0.0, 1.0]``.

        Returns 0.0 when there was no speculation chain to evaluate.
        """
        if self.chain_length == 0:
            return 0.0
        return self.chain_accept_count / self.chain_length

    @property
    def tokens_emitted(self) -> int:
        """Tokens produced by this verify call.

        Equals ``chain_accept_count + 1`` (the +1 is the bonus token).
        """
        return self.chain_accept_count + 1


def verify_speculation(
    speculation_root: SpeculationNode | None,
    oracle: Oracle,
    context: list[int] | tuple[int, ...],
) -> VerifyResult:
    """Walk a linear speculation chain and decide what to keep.

    Args:
        speculation_root: root of the speculation chain, or ``None`` if no
            speculation was proposed (e.g., proposer returned no candidate).
            For C0, the chain must be linear (each node has 0 or 1 children);
            ``ValueError`` is raised if a branching tree is passed.
        oracle: callable that, given a context list, returns the true next
            token id.
        context: tokens preceding the position the speculation starts from.

    Returns:
        A ``VerifyResult`` with the tokens to commit + acceptance counts.
    """
    ctx = list(context)

    if speculation_root is None:
        bonus = oracle(ctx)
        return VerifyResult(
            accepted_tokens=[bonus],
            chain_accept_count=0,
            chain_length=0,
        )

    chain = speculation_root.to_linear_chain()  # raises if non-linear
    chain_length = len(chain)
    accepted: list[int] = []

    for idx, spec_token in enumerate(chain):
        oracle_token = oracle(ctx + accepted)
        if oracle_token == spec_token:
            accepted.append(spec_token)
            continue
        # Mismatch at idx: accept oracle_token as bonus, stop.
        accepted.append(oracle_token)
        return VerifyResult(
            accepted_tokens=accepted,
            chain_accept_count=idx,
            chain_length=chain_length,
        )

    # Whole chain accepted: ask the oracle once more for the +1 bonus.
    bonus = oracle(ctx + accepted)
    accepted.append(bonus)
    return VerifyResult(
        accepted_tokens=accepted,
        chain_accept_count=chain_length,
        chain_length=chain_length,
    )


# ---------------------------------------------------------------------------
# C1 phase: real-model batch verify primitive
# ---------------------------------------------------------------------------
#
# This section adds an mlx-lm-backed implementation of the verifier. The
# C0 unit tests don't import this — they use the synthetic Oracle abstraction
# above. We keep mlx imports lazy so C0 tests remain pure-Python.
#
# See docs/architect/design/F-2-ngram-suffix-spec.md §4.2.


def mlx_lm_batch_verify(
    model: object,
    context_ids: list[int],
    chain_ids: list[int],
) -> VerifyResult:
    """Verify a speculation chain against an mlx-lm model in one batch.

    Uses two forward passes per call:
      1. Prefill ``context_ids`` to populate the cache and grab the logit at
         the last context position (= oracle prediction for ``chain_ids[0]``).
      2. Forward ``chain_ids`` to get per-position logits. The logit at chain
         position ``i`` is the oracle prediction for ``chain_ids[i+1]`` (or
         the +1 bonus token if ``i == len(chain) - 1`` and we got that far).

    A real production integration would amortize step 1 across many verify
    calls by reusing the cache. For the C1 canary we re-prefill each call so
    the function is self-contained and easy to measure.

    Args:
        model: an mlx-lm-loaded model (from ``mlx_lm.load``).
        context_ids: tokens preceding the speculation.
        chain_ids: candidate tokens to verify. May be empty, in which case
            the function returns just the oracle's first prediction.

    Returns:
        ``VerifyResult`` with the same shape produced by ``verify_speculation``.
    """
    import mlx.core as mx  # lazy import: keeps C0 tests mlx-free
    from mlx_lm.models.cache import make_prompt_cache

    if not context_ids:
        raise ValueError("mlx_lm_batch_verify requires a non-empty context")

    cache = make_prompt_cache(model)

    # NOTE on prefill shape (2026-05-26 C1 canary finding):
    # mlx-lm has a small numerical drift between
    #   (a) one batched forward of the full context, taking logits[-1]
    #   (b) prefilling n-1 tokens then forwarding the last token, taking that logit
    # All split / chunked variants agree with each other and with
    # ``mlx_lm.stream_generate``; only (a) is the outlier. To stay
    # consistent with the standard non-speculative serving path, we prefill
    # ``context[:-1]`` and then forward ``context[-1]`` as the source of
    # ``last_context_logit``. The extra forward is amortized in production
    # (prefill done once per request, cache reused for many verify calls).
    head = context_ids[:-1]
    tail = [context_ids[-1]]
    if head:
        prefill_head_arr = mx.array([head], dtype=mx.uint32)
        model(prefill_head_arr, cache=cache)
        mx.eval([c.state for c in cache])
    tail_arr = mx.array([tail], dtype=mx.uint32)
    last_step_logits = model(tail_arr, cache=cache)
    last_context_logit = last_step_logits[0, -1]
    mx.eval(last_context_logit)

    if not chain_ids:
        bonus = int(mx.argmax(last_context_logit).item())
        return VerifyResult(
            accepted_tokens=[bonus],
            chain_accept_count=0,
            chain_length=0,
        )

    chain_array = mx.array([chain_ids], dtype=mx.uint32)
    chain_logits = model(chain_array, cache=cache)
    mx.eval(chain_logits)

    chain_length = len(chain_ids)
    accepted: list[int] = []

    # Position 0 of the chain: oracle prediction comes from last_context_logit.
    oracle_for_chain_0 = int(mx.argmax(last_context_logit).item())
    if oracle_for_chain_0 != chain_ids[0]:
        return VerifyResult(
            accepted_tokens=[oracle_for_chain_0],
            chain_accept_count=0,
            chain_length=chain_length,
        )
    accepted.append(chain_ids[0])

    # Positions 1..N-1: oracle predictions come from chain_logits[0, 0..N-2].
    for i in range(1, chain_length):
        oracle_for_chain_i = int(mx.argmax(chain_logits[0, i - 1]).item())
        if oracle_for_chain_i != chain_ids[i]:
            accepted.append(oracle_for_chain_i)
            return VerifyResult(
                accepted_tokens=accepted,
                chain_accept_count=i,
                chain_length=chain_length,
            )
        accepted.append(chain_ids[i])

    # All chain tokens accepted: bonus comes from chain_logits[0, N-1].
    bonus = int(mx.argmax(chain_logits[0, chain_length - 1]).item())
    accepted.append(bonus)
    return VerifyResult(
        accepted_tokens=accepted,
        chain_accept_count=chain_length,
        chain_length=chain_length,
    )
