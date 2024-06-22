"""Class that ties all components together.
"""
from dataclasses import dataclass

from omoide.domain import interfaces


@dataclass()
class Mediator:
    """Class that ties all components together.
    """
    users_repo: interfaces.AbsUsersRepository
    items_repo: interfaces.AbsItemsReadRepository
