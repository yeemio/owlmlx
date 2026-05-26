"""C0 phase unit tests for the n-gram speculative decoding module.

Covers:

- ``NgramSuffixTree`` ingest / lookup invariants on synthetic sequences
  (including a randomised N=1000 brute-force ground-truth comparison).
- ``NgramProposer`` linear chain shape contract.
- ``verify_speculation`` accept/reject correctness across the canonical
  cases: no speculation, full accept, partial accept, mismatch at first,
  empty store.
- Public ``VerifyResult`` derived properties (acceptance_rate,
  tokens_emitted).

These tests are pure-Python, do not load any model, and run in milliseconds.
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable

import pytest

from owlmlx.speculative.suffix_decoding import (
    NgramProposer,
    NgramSuffixTree,
    SpeculationNode,
    VerifyResult,
    verify_speculation,
)


# ----------------------------------------------------------------------------
# NgramSuffixTree
# ----------------------------------------------------------------------------


class TestNgramSuffixTreeBasics:
    def test_empty_store_returns_no_lookup(self) -> None:
        tree = NgramSuffixTree()
        assert tree.lookup([1, 2, 3]) == []

    def test_lookup_empty_context_returns_empty(self) -> None:
        tree = NgramSuffixTree()
        tree.ingest([1, 2, 3])
        assert tree.lookup([]) == []

    def test_lookup_top_k_zero_returns_empty(self) -> None:
        tree = NgramSuffixTree()
        tree.ingest([1, 2, 3])
        assert tree.lookup([1, 2], top_k=0) == []

    def test_invalid_max_n_raises(self) -> None:
        with pytest.raises(ValueError):
            NgramSuffixTree(max_n=0)

    def test_total_tokens_tracks_ingest_lengths(self) -> None:
        tree = NgramSuffixTree()
        tree.ingest([1, 2, 3])
        tree.ingest([4, 5])
        assert tree.total_tokens() == 5

    def test_basic_continuation_lookup(self) -> None:
        tree = NgramSuffixTree(max_n=4)
        tree.ingest([1, 2, 3, 1, 2, 4])
        results = tree.lookup([1, 2], top_k=4)
        token_set = {t for t, _ in results}
        assert token_set == {3, 4}

    def test_frequency_ordering(self) -> None:
        tree = NgramSuffixTree(max_n=2)
        # context (1, 2) followed by 3 three times, 4 once
        tree.ingest([1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 4])
        results = tree.lookup([1, 2], top_k=2)
        assert results[0][0] == 3
        assert results[0][1] == 3
        assert results[1][0] == 4
        assert results[1][1] == 1

    def test_longest_suffix_takes_priority(self) -> None:
        tree = NgramSuffixTree(max_n=3)
        tree.ingest([5, 5, 5, 5, 9])  # context (5,5,5) → 5 then 9
        tree.ingest([7, 5, 5, 5, 1])  # context (5,5,5) → 1
        # context (5,5,5) should hit longest 3-gram suffix, not 1-gram
        results = tree.lookup([99, 5, 5, 5], top_k=4)
        token_set = {t for t, _ in results}
        # the 3-gram (5,5,5) → {5: 1, 9: 1, 1: 1}; shorter suffixes are
        # not consulted because the 3-gram matched first
        assert token_set == {5, 9, 1}

    def test_total_ngrams_grows_with_ingest(self) -> None:
        tree = NgramSuffixTree(max_n=2)
        before = tree.total_ngrams()
        tree.ingest([1, 2, 3, 4, 5])
        after = tree.total_ngrams()
        assert after > before


class TestNgramSuffixTreeInvariants:
    """N=1000 randomised sequences vs brute-force ground truth."""

    @staticmethod
    def _brute_force_continuations(
        history: list[list[int]],
        context: list[int],
        max_n: int,
    ) -> Counter[int]:
        """Reference implementation: scan all positions in all sequences,
        find every occurrence of any suffix of `context` (longest first),
        and tally what follows. Returns the longest-suffix tally only.
        """
        for n in range(min(max_n, len(context)), 0, -1):
            tally: Counter[int] = Counter()
            key = tuple(context[-n:])
            for seq in history:
                for i in range(len(seq) - n):
                    if tuple(seq[i : i + n]) == key:
                        tally[seq[i + n]] += 1
            if tally:
                return tally
        return Counter()

    def test_random_sequences_match_brute_force(self) -> None:
        rng = random.Random(0xC0)
        max_n = 4
        tree = NgramSuffixTree(max_n=max_n)
        history: list[list[int]] = []
        # Ingest 50 sequences of length 20, drawn from a 12-token vocabulary.
        # Low vocabulary maximises ngram-collision coverage.
        for _ in range(50):
            seq = [rng.randint(0, 11) for _ in range(20)]
            history.append(seq)
            tree.ingest(seq)

        # Run 1000 random lookups and compare to brute force.
        mismatches: list[tuple[list[int], list[tuple[int, int]], Counter[int]]] = []
        for _ in range(1000):
            ctx_len = rng.randint(1, max_n + 2)
            ctx = [rng.randint(0, 11) for _ in range(ctx_len)]
            tree_results = tree.lookup(ctx, top_k=64)
            brute = self._brute_force_continuations(history, ctx, max_n)
            tree_counter: Counter[int] = Counter()
            for tok, freq in tree_results:
                tree_counter[tok] = freq
            if tree_counter != brute:
                mismatches.append((ctx, tree_results, brute))
        assert not mismatches, (
            f"first mismatch out of {len(mismatches)} of 1000 lookups: "
            f"{mismatches[0]}"
        )


# ----------------------------------------------------------------------------
# NgramProposer
# ----------------------------------------------------------------------------


class TestNgramProposer:
    def test_no_match_returns_none(self) -> None:
        tree = NgramSuffixTree()
        proposer = NgramProposer(store=tree, max_depth=3)
        assert proposer.propose([99, 99, 99]) is None

    def test_invalid_max_depth_raises(self) -> None:
        tree = NgramSuffixTree()
        with pytest.raises(ValueError):
            NgramProposer(store=tree, max_depth=0)

    def test_invalid_min_frequency_raises(self) -> None:
        tree = NgramSuffixTree()
        with pytest.raises(ValueError):
            NgramProposer(store=tree, min_frequency=0)

    def test_below_min_frequency_returns_none(self) -> None:
        tree = NgramSuffixTree(max_n=2)
        tree.ingest([1, 2, 3])  # (1,2) → 3 with frequency 1
        proposer = NgramProposer(store=tree, min_frequency=2)
        assert proposer.propose([1, 2]) is None

    def test_linear_chain_construction(self) -> None:
        tree = NgramSuffixTree(max_n=4)
        # Reinforce a stable path (1,2) → 3 → 4 → 5
        for _ in range(3):
            tree.ingest([1, 2, 3, 4, 5])
        proposer = NgramProposer(store=tree, max_depth=3, min_frequency=1)
        root = proposer.propose([1, 2])
        assert root is not None
        chain = root.to_linear_chain()
        assert chain == [3, 4, 5]

    def test_max_depth_caps_chain_length(self) -> None:
        tree = NgramSuffixTree(max_n=4)
        for _ in range(3):
            tree.ingest([1, 2, 3, 4, 5, 6, 7, 8])
        proposer = NgramProposer(store=tree, max_depth=2)
        root = proposer.propose([1, 2])
        assert root is not None
        chain = root.to_linear_chain()
        assert len(chain) == 2

    def test_chain_short_when_history_runs_out(self) -> None:
        tree = NgramSuffixTree(max_n=2)
        tree.ingest([1, 2, 3])  # only 1 step of continuation from (1,2)
        proposer = NgramProposer(store=tree, max_depth=5, min_frequency=1)
        root = proposer.propose([1, 2])
        assert root is not None
        chain = root.to_linear_chain()
        # First step: 3. After 3, context becomes (2, 3); store has no
        # continuation from (2, 3) within max_n=2 → chain stops.
        # But (3,) exists too if seq is [1,2,3]? No, position 2 is the
        # last; nothing follows. So no (3,) → next entry.
        assert chain == [3]

    def test_speculation_node_depth_property(self) -> None:
        leaf = SpeculationNode(token_id=99)
        assert leaf.depth() == 1
        mid = SpeculationNode(token_id=42, children=[leaf])
        assert mid.depth() == 2
        root = SpeculationNode(token_id=7, children=[mid])
        assert root.depth() == 3

    def test_to_linear_chain_rejects_branching(self) -> None:
        node = SpeculationNode(
            token_id=1,
            children=[
                SpeculationNode(token_id=2),
                SpeculationNode(token_id=3),
            ],
        )
        with pytest.raises(ValueError):
            node.to_linear_chain()


# ----------------------------------------------------------------------------
# verify_speculation
# ----------------------------------------------------------------------------


def _scripted_oracle(script: dict[tuple[int, ...], int]) -> Callable[[list[int]], int]:
    """Build an oracle that returns predetermined tokens for predetermined
    context-token tuples. Raises if asked a context not in the script.
    """

    def _oracle(ctx: list[int]) -> int:
        key = tuple(ctx)
        if key not in script:
            raise KeyError(f"oracle has no scripted answer for context {key}")
        return script[key]

    return _oracle


def _linear_speculation(*tokens: int) -> SpeculationNode:
    nodes = [SpeculationNode(token_id=t) for t in tokens]
    for i in range(len(nodes) - 1):
        nodes[i].children.append(nodes[i + 1])
    return nodes[0]


class TestVerifySpeculation:
    def test_no_speculation_returns_oracle_token_as_bonus(self) -> None:
        oracle = _scripted_oracle({(1, 2): 42})
        result = verify_speculation(None, oracle, [1, 2])
        assert result.accepted_tokens == [42]
        assert result.chain_accept_count == 0
        assert result.chain_length == 0
        assert result.tokens_emitted == 1
        assert result.acceptance_rate == 0.0

    def test_full_chain_accepted_plus_bonus(self) -> None:
        # Speculation [10, 20, 30]; oracle agrees on each.
        oracle = _scripted_oracle(
            {
                (1, 2): 10,
                (1, 2, 10): 20,
                (1, 2, 10, 20): 30,
                (1, 2, 10, 20, 30): 99,  # bonus after chain
            }
        )
        result = verify_speculation(
            _linear_speculation(10, 20, 30), oracle, [1, 2]
        )
        assert result.accepted_tokens == [10, 20, 30, 99]
        assert result.chain_accept_count == 3
        assert result.chain_length == 3
        assert result.tokens_emitted == 4
        assert result.acceptance_rate == 1.0

    def test_partial_accept_then_mismatch(self) -> None:
        # Speculation [10, 20, 30]; oracle accepts 10, 20 then says 77.
        oracle = _scripted_oracle(
            {
                (1, 2): 10,
                (1, 2, 10): 20,
                (1, 2, 10, 20): 77,  # disagrees with 30
            }
        )
        result = verify_speculation(
            _linear_speculation(10, 20, 30), oracle, [1, 2]
        )
        assert result.accepted_tokens == [10, 20, 77]
        assert result.chain_accept_count == 2
        assert result.chain_length == 3
        assert result.tokens_emitted == 3
        assert abs(result.acceptance_rate - (2 / 3)) < 1e-9

    def test_mismatch_at_first_position(self) -> None:
        oracle = _scripted_oracle({(1, 2): 99})
        result = verify_speculation(
            _linear_speculation(10, 20, 30), oracle, [1, 2]
        )
        assert result.accepted_tokens == [99]
        assert result.chain_accept_count == 0
        assert result.chain_length == 3
        assert result.tokens_emitted == 1

    def test_single_token_chain_accepted(self) -> None:
        oracle = _scripted_oracle({(1, 2): 7, (1, 2, 7): 8})
        result = verify_speculation(_linear_speculation(7), oracle, [1, 2])
        assert result.accepted_tokens == [7, 8]
        assert result.chain_accept_count == 1
        assert result.chain_length == 1

    def test_branching_tree_rejected(self) -> None:
        # verifier delegates linearity check to to_linear_chain; verify it
        # propagates the ValueError instead of silently picking a branch.
        node = SpeculationNode(
            token_id=1,
            children=[
                SpeculationNode(token_id=2),
                SpeculationNode(token_id=3),
            ],
        )
        with pytest.raises(ValueError):
            verify_speculation(node, lambda ctx: 0, [])


# ----------------------------------------------------------------------------
# End-to-end: proposer → verifier flow
# ----------------------------------------------------------------------------


class TestEndToEnd:
    def test_chain_built_from_history_is_fully_accepted_by_history_oracle(
        self,
    ) -> None:
        """When the oracle answers using the same history the proposer
        learned from, the chain should match perfectly and accept fully.
        """
        history_sequence = [1, 2, 3, 4, 5, 6, 7, 8]
        tree = NgramSuffixTree(max_n=4)
        for _ in range(5):
            tree.ingest(history_sequence)

        proposer = NgramProposer(store=tree, max_depth=4, min_frequency=1)
        chain_root = proposer.propose([1, 2])
        assert chain_root is not None

        # Oracle: given context, return the next token from history_sequence
        # if the context's tail matches a prefix of history_sequence.
        def history_oracle(ctx: list[int]) -> int:
            for k in range(len(history_sequence) - 1, 0, -1):
                if ctx[-k:] == history_sequence[:k]:
                    return history_sequence[k]
            # fall back to "next position in the canonical sequence"
            return history_sequence[len(ctx) % len(history_sequence)]

        result = verify_speculation(chain_root, history_oracle, [1, 2])
        # All 4 chain tokens should be accepted; plus 1 bonus.
        assert result.chain_accept_count == 4
        assert result.chain_length == 4
        assert result.tokens_emitted == 5
