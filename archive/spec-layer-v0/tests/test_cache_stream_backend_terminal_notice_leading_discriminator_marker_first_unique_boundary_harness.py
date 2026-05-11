from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness,
)


def test_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness_observes_boundary() -> None:
    result = (
        run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness()
    )

    assert (
        result.backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible
        is True
    )
    assert (
        result.leading_discriminator_marker_first_unique_boundary_status
        == "backend_terminal_notice_leading_discriminator_marker_discriminant_is_first_unique_boundary_visible"
    )
    assert result.shared_non_unique_prefix == '{"ok": true, "terminal_notice'
    assert result.first_unique_boundary_prefix == '{"ok": true, "terminal_notice_'
    assert result.earlier_prefix_collides_with_old_notice_record is True
