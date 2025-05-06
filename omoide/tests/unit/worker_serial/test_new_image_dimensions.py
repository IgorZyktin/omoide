"""Tests."""

import pytest

from omoide.workers.serial.use_cases.upload_use_cases import get_new_image_dimensions


@pytest.mark.parametrize(
    ('old_width', 'old_height', 'target_size', 'ref_width', 'ref_height'),
    [
        (100, 100, 100, 100, 100),
        (200, 200, 100, 100, 100),
        (1024, 256, 128, 128, 32),
        (256, 1024, 128, 32, 128),
    ],
)
def test_new_image_dimensions(old_width, old_height, target_size, ref_width, ref_height):
    """Must resize correctly."""
    result = get_new_image_dimensions(old_width, old_height, target_size)
    assert result == (ref_width, ref_height)
