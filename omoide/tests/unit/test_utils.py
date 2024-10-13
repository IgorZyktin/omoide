"""Tests."""

from uuid import UUID

import pytest

from omoide import utils


@pytest.mark.parametrize(('uuid', 'length', 'result'), [
    ('fb6a8840-d6a8-4ab4-9555-be67917c8717', 2, 'fb'),
    (UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717'), 3, 'fb6'),
])
def test_get_bucket(uuid, length, result):
    """Must cut symbols from the start, but only if input is UUID."""
    assert utils.get_bucket(uuid, length) == result


@pytest.mark.parametrize(('uuid', 'result'), [
    ('something', False),
    (UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717'), True),
    ('fb6a8840-d6a8-4ab4-9555-be67917c8717', True),
])
def test_is_valid_uuid(uuid, result):
    """Must validate UUIDs and skip random strings."""
    assert utils.is_valid_uuid(uuid) is result


@pytest.mark.parametrize(('size', 'reference'), [
    (-2_000, '-2.0 КиБ'),
    (-2_048, '-2.0 КиБ'),
    (0, '0 Б'),
    (27, '27 Б'),
    (999, '999 Б'),
    (1_000, '1000 Б'),
    (1_023, '1023 Б'),
    (1_024, '1.0 КиБ'),
    (1_728, '1.7 КиБ'),
    (110_592, '108.0 КиБ'),
    (1_000_000, '976.6 КиБ'),
    (7_077_888, '6.8 МиБ'),
    (452_984_832, '432.0 МиБ'),
    (1_000_000_000, '953.7 МиБ'),
    (28_991_029_248, '27.0 ГиБ'),
    (1_855_425_871_872, '1.7 ТиБ'),
    (9_223_372_036_854_775_807, '8.0 ЭиБ'),
])
def test_human_readable_size_ru(size, reference):
    """Must convert to readable size in russian."""
    assert utils.human_readable_size(size, language='RU') == reference


@pytest.mark.parametrize(('size', 'reference'), [
    (-2_000, '-2.0 KiB'),
    (-2_048, '-2.0 KiB'),
    (0, '0 B'),
    (27, '27 B'),
    (999, '999 B'),
    (1_000, '1000 B'),
    (1_023, '1023 B'),
    (1_024, '1.0 KiB'),
    (1_728, '1.7 KiB'),
    (110_592, '108.0 KiB'),
    (1_000_000, '976.6 KiB'),
    (7_077_888, '6.8 MiB'),
    (452_984_832, '432.0 MiB'),
    (1_000_000_000, '953.7 MiB'),
    (28_991_029_248, '27.0 GiB'),
    (1_855_425_871_872, '1.7 TiB'),
    (9_223_372_036_854_775_807, '8.0 EiB'),
])
def test_human_readable_size_en(size, reference):
    """Must convert to readable size in english."""
    assert utils.human_readable_size(size, language='EN') == reference


@pytest.mark.parametrize(('seconds', 'reference'), [
    (0, '0s'),
    (1, '1s'),
    (60, '1m'),
    (100, '1m 40s'),
    (900, '15m'),
    (2_760, '46m'),
    (86_400, '1d'),
    (99_658, '1d 3h 40m 58s'),
])
def test_human_readable_time(seconds, reference):
    """Must convert seconds into human-readable time."""
    assert utils.human_readable_time(seconds) == reference


def test_split():
    """Must separate string and filter out empty values."""
    reference = ['a', 'b', 'c']
    result = utils.split(',a,b,,c,')

    assert result == reference


def test_sep_digits():
    """Must separate digits on 1000s."""
    assert utils.sep_digits('12345678') == '12345678'
    assert utils.sep_digits(12345678) == '12 345 678'
    assert utils.sep_digits(1234.5678) == '1 234.57'
    assert utils.sep_digits(1234.5678, precision=4) == '1 234.5678'
    assert utils.sep_digits(1234.0, precision=4) == '1 234.0000'
    assert utils.sep_digits(1234.0, precision=0) == '1 234'
