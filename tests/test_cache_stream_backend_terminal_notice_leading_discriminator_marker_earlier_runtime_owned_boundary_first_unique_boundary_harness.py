from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness_observes_boundary() -> None:
    result = (
        run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness()
    )

    assert (
        result.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_visible
        is True
    )
    assert (
        result.leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_status
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_is_first_honest_unique_boundary_visible"
    )
    assert result.shared_non_unique_prefix == '{"ok": true, "runtime_owned_terminal_'
    assert (
        result.first_honest_unique_boundary_prefix
        == '{"ok": true, "runtime_owned_terminal_b'
    )
    assert result.earlier_literal_prefix_is_not_runtime_owned_boundary is True
