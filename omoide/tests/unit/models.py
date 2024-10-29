"""Tests."""

from dataclasses import dataclass

from omoide import models


@dataclass(kw_only=True)
class Changeable(models.ChangesMixin):
    """Demo-object."""
    x: str
    y: int = 2
    z: int = 3


def test_changes_mixin_nothing():
    # arrange
    obj = Changeable(x='a')

    # assert
    assert obj.x == 'a'
    assert obj.y == 2
    assert obj.z == 3
    assert not obj.what_changed()


def test_changes_mixin_field():
    # arrange
    obj = Changeable(x='a')

    # act
    obj.x = 'b'

    # assert
    assert obj.x == 'b'
    assert obj.y == 2
    assert obj.z == 3
    assert obj.what_changed() == {'x': 'b'}


def test_changes_mixin_reset():
    # arrange
    obj = Changeable(x='a')

    # act
    obj.x = 'b'

    # assert
    assert obj.what_changed() == {'x': 'b'}
    obj.reset_changes()
    assert not obj.what_changed()
