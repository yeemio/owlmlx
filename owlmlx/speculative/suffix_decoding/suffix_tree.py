"""Compact n-gram suffix store.

For C0, this is implemented as an n-gram counter (dict of context tuples to
Counter of next tokens). The interface is suffix-tree-like: ingest token
sequences, then given a context look up the most frequent continuations.

The true compact suffix tree with ~10.75 bytes/token footprint (paper:
SuffixDecoding, arxiv 2411.04975) is a memory-efficiency optimization that
is **out of scope for C0**. Replacing the backing store later does not
change the public ``ingest`` / ``lookup`` shape; tests should not depend on
internal layout.

This module imports nothing model-related. It is pure-Python and used by
C0 unit tests as well as by ``proposer.py``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class NgramSuffixTree:
    """Token-history store indexed by short contexts.

    For every position ``i`` in an ingested sequence and every context
    length ``n`` in ``1..max_n``, the entry ``ngrams[tokens[i-n:i]]`` is
    incremented for ``next_token = tokens[i]``.

    Look up by passing a recent token context; the longest matching suffix
    of that context is used to return its top-k continuations.

    Attributes:
        max_n: maximum context length tracked (inclusive). Defaults to 8.
            Larger values trade memory for prediction sharpness.
    """

    max_n: int = 8
    _ngrams: dict[tuple[int, ...], Counter[int]] = field(default_factory=dict)
    _total_tokens_ingested: int = 0

    def __post_init__(self) -> None:
        if self.max_n < 1:
            raise ValueError(f"max_n must be >= 1, got {self.max_n}")

    def ingest(self, tokens: Iterable[int]) -> None:
        """Add a token sequence to the store.

        Position 0 has no context; positions 1..len-1 contribute n-grams
        for every context length 1..min(max_n, i).
        """
        seq = list(tokens)
        self._total_tokens_ingested += len(seq)
        for i in range(1, len(seq)):
            next_token = seq[i]
            upper = min(self.max_n, i)
            for n in range(1, upper + 1):
                context = tuple(seq[i - n : i])
                counter = self._ngrams.get(context)
                if counter is None:
                    counter = Counter()
                    self._ngrams[context] = counter
                counter[next_token] += 1

    def lookup(
        self, context: list[int] | tuple[int, ...], top_k: int = 4
    ) -> list[tuple[int, int]]:
        """Return top-k continuations of the longest matching context suffix.

        Each result is ``(token_id, frequency)``. Tied frequencies preserve
        Counter insertion order (i.e., the order in which they were first
        seen during ingest). Returns ``[]`` when no suffix of ``context``
        matches an ingested n-gram.

        Args:
            context: ordered tokens preceding the position we want to predict.
            top_k: maximum number of continuations to return.

        Returns:
            A list of (token_id, frequency) sorted by frequency descending.
        """
        if top_k <= 0:
            return []
        if not context:
            return []
        max_lookup_n = min(self.max_n, len(context))
        for n in range(max_lookup_n, 0, -1):
            key = tuple(context[-n:])
            counter = self._ngrams.get(key)
            if counter is not None:
                return counter.most_common(top_k)
        return []

    def total_tokens(self) -> int:
        """Total number of tokens passed to ``ingest`` (with multiplicity)."""
        return self._total_tokens_ingested

    def total_ngrams(self) -> int:
        """Distinct context keys currently stored."""
        return len(self._ngrams)
