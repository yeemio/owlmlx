"""Speculative decoding strategies for owlmlx.

Houses runtime-owned speculative method implementations. Each sub-package
implements one ``method`` value from the F-1 surface vocabulary (see
``docs/architect/design/F-1-spec.md`` §4.5).

C0 phase (offline verifier, no model dependency) lives under
``suffix_decoding/``. C1 (mlx-lm canary) and C2 (serving integration) are
added in later phases per ``docs/architect/design/F-2-ngram-suffix-spec.md``.
"""
