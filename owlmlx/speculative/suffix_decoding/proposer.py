"""Build a speculation chain from a suffix store + current context.

The proposer takes the recent token context and uses the suffix store to
build a forward-looking chain of candidate next tokens. C0 only supports
**linear chains** (one branch per level); tree-shaped speculation is a C2
extension and intentionally not implemented here.

Algorithm (linear chain):

1. Look up context in the suffix store, take the highest-frequency continuation.
2. If found and its frequency is at or above ``min_frequency``, emit it as
   the root of the chain.
3. Append the candidate to the context and recurse, stopping at
   ``max_depth`` or when no candidate meets the threshold.

This file imports nothing model-related; it works entirely off of the
``NgramSuffixTree`` data structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from owlmlx.speculative.suffix_decoding.suffix_tree import NgramSuffixTree


@dataclass
class SpeculationNode:
    """One node in the speculation tree.

    For C0 linear chains, each node has at most one child. The type still
    supports lists of children so the same shape can carry tree-shaped
    speculation in later phases without a public-API break.

    Attributes:
        token_id: candidate next token at this position.
        frequency: how often this token followed the path leading here in
            the ingested histories. Equal-to-zero is legal (means the
            frequency was not recorded, e.g. from a synthetic test).
        children: deeper speculation branches. Empty list = leaf.
    """

    token_id: int
    frequency: int = 0
    children: list["SpeculationNode"] = field(default_factory=list)

    def depth(self) -> int:
        """Maximum depth of the subtree rooted here (leaf = 1)."""
        if not self.children:
            return 1
        return 1 + max(child.depth() for child in self.children)

    def to_linear_chain(self) -> list[int]:
        """Flatten to a list of token ids assuming the tree is a chain.

        Raises ValueError if any node has more than one child.
        """
        chain: list[int] = []
        node: SpeculationNode | None = self
        while node is not None:
            chain.append(node.token_id)
            if not node.children:
                node = None
            elif len(node.children) == 1:
                node = node.children[0]
            else:
                raise ValueError(
                    "to_linear_chain called on non-linear speculation tree"
                )
        return chain


@dataclass
class NgramProposer:
    """Build a linear speculation chain from a suffix store.

    Attributes:
        store: the ``NgramSuffixTree`` to query.
        max_depth: maximum chain length to propose (inclusive). 1 = single
            token; 4 is a reasonable default for C0 experimentation.
        min_frequency: a candidate is only proposed when its observed
            frequency in the store is at least this value. 1 = accept any
            seen continuation; higher values reduce speculation noise.
    """

    store: NgramSuffixTree
    max_depth: int = 4
    min_frequency: int = 1

    def __post_init__(self) -> None:
        if self.max_depth < 1:
            raise ValueError(f"max_depth must be >= 1, got {self.max_depth}")
        if self.min_frequency < 1:
            raise ValueError(
                f"min_frequency must be >= 1, got {self.min_frequency}"
            )

    def propose(
        self, context: Iterable[int]
    ) -> SpeculationNode | None:
        """Build a linear speculation chain for the given context.

        Returns the root ``SpeculationNode`` of the chain, or ``None`` if
        no continuation in the store meets the ``min_frequency`` threshold
        at the very first step.

        Args:
            context: recent token ids preceding the position to predict.
                Iterated to a list internally; not consumed in place.
        """
        ctx = list(context)
        first = self._pick_one(ctx)
        if first is None:
            return None
        root = SpeculationNode(token_id=first[0], frequency=first[1])
        current = root
        extended_ctx = ctx + [first[0]]
        for _ in range(self.max_depth - 1):
            picked = self._pick_one(extended_ctx)
            if picked is None:
                break
            child = SpeculationNode(token_id=picked[0], frequency=picked[1])
            current.children.append(child)
            current = child
            extended_ctx = extended_ctx + [picked[0]]
        return root

    def _pick_one(self, context: list[int]) -> tuple[int, int] | None:
        candidates = self.store.lookup(context, top_k=1)
        if not candidates:
            return None
        token_id, frequency = candidates[0]
        if frequency < self.min_frequency:
            return None
        return token_id, frequency
