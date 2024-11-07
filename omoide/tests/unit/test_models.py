"""Tests."""

from dataclasses import dataclass
from typing import Any
from typing import Collection
from typing import Self

from omoide import models


@dataclass
class Changeable(models.OmoideModel):
    """Demo-object."""

    x: str
    y: int = 2
    z: int = 3

    @classmethod
    def from_obj(
        cls,
        obj: Any,
        extra_keys: Collection[str] = (),
        extras: dict[str, Any] | None = None,
    ) -> Self:
        """Create instance from arbitrary object."""
        _ = extra_keys
        _ = extras
        return cls(
            x=obj.x,
            y=obj.y,
            z=obj.z,
        )


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
    assert obj.what_changed() == {'x'}
    assert obj.get_changes() == {'x': 'b'}


def test_changes_mixin_reset():
    # arrange
    obj = Changeable(x='a')

    # act
    obj.x = 'b'

    # assert
    assert obj.what_changed() == {'x'}
    assert obj.get_changes() == {'x': 'b'}
    obj.reset_changes()
    assert not obj.what_changed()
    assert not obj.get_changes()
