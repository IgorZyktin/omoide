"""Tests.
"""
from uuid import UUID

import pydantic
import pytest

from omoide import utils
from omoide.utils import serialize_model


@pytest.mark.parametrize('uuid,length,result', [
    ('fb6a8840-d6a8-4ab4-9555-be67917c8717', 2, 'fb'),
    (UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717'), 3, 'fb6'),
])
def test_get_bucket(uuid, length, result):
    """Must cut symbols from the start, but only if input is UUID."""
    assert utils.get_bucket(uuid, length) == result


@pytest.mark.parametrize('uuid,result', [
    ('something', False),
    (UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717'), True),
    ('fb6a8840-d6a8-4ab4-9555-be67917c8717', True),
])
def test_is_valid_uuid(uuid, result):
    """Must validate UUIDs and skip random strings."""
    assert utils.is_valid_uuid(uuid) is result


@pytest.mark.parametrize('uuid,result', [
    (None,
     None),
    ('something',
     None),
    (UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717'),
     UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717')),
    ('fb6a8840-d6a8-4ab4-9555-be67917c8717',
     UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717')),
])
def test_cast_uuid(uuid, result):
    """Must convert to UUID or None."""
    assert utils.cast_uuid(uuid) == result


@pytest.mark.parametrize('size, reference', [
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
def test_byte_count_to_text_ru(size, reference):
    """Must convert to readable size in russian."""
    assert utils.byte_count_to_text(size, language='RU') == reference


@pytest.mark.parametrize('size, reference', [
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
def test_byte_count_to_text_en(size, reference):
    """Must convert to readable size in english."""
    assert utils.byte_count_to_text(size, language='EN') == reference


@pytest.mark.parametrize('seconds, reference', [
    (0, '0s'),
    (1, '1s'),
    (60, '1m'),
    (100, '1m 40s'),
    (900, '15m'),
    (2_760, '46m'),
    (86_400, '1d'),
    (99_658, '1d 3h 40m 58s'),
])
def test_format_as_human_readable_time(seconds, reference):
    """Must convert seconds into human-readable time."""
    assert utils.human_readable_time(seconds) == reference


@pytest.fixture
def config_like_model():
    class SubNested(pydantic.BaseModel):
        k: str = 'value'
        f: dict = pydantic.Field(default={'something': 'else'})

    class Nested(pydantic.BaseModel):
        x: str = 'other'
        y: dict = pydantic.Field(default={'key': 'value'})
        sub_nested: SubNested = SubNested()

    class Model(pydantic.BaseModel):
        a: int = 1
        b: str = 'var'
        nested: Nested = Nested()

    return Model()


@pytest.fixture
def config_like_dict():
    return {
        'a': 1,
        'b': 'var',
        'nested': {
            'x': 'other',
            'y': {'key': 'value'},
            'sub_nested': {
                'k': 'value',
                'f': {'something': 'else'},
            }
        }
    }


@pytest.fixture
def serialization_reference():
    return """
a=1
b='var'
nested:
    x='other'
    y={'key': 'value'}
    sub_nested:
        k='value'
        f={'something': 'else'}
    """.strip()


def test_serialize_model_pydantic(config_like_model, serialization_reference):
    """Must serialize properly."""
    result = serialize_model(config_like_model,
                             do_not_serialize=frozenset(('y', 'f')))

    assert result == serialization_reference


def test_serialize_model_dict(config_like_dict, serialization_reference):
    """Must serialize properly."""
    result = serialize_model(config_like_dict,
                             do_not_serialize=frozenset(('y', 'f')))

    assert result == serialization_reference


def test_split():
    """Must separate string and filter out empty values."""
    reference = ['a', 'b', 'c']
    result = utils.split(',a,b,,c,')

    assert result == reference
