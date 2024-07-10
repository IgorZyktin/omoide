"""Class that ties all components together."""
from dataclasses import dataclass

# FIXME - make uniform import path
from omoide.domain.interfaces import AbsItemsRepo
from omoide.domain.interfaces import AbsSearchRepository
from omoide.storage import interfaces


@dataclass()
class Mediator:
    """Class that ties all components together."""
    exif_repo: interfaces.AbsEXIFRepository
    items_repo: AbsItemsRepo
    meta_repo: interfaces.AbsMetainfoRepo
    misc_repo: interfaces.AbsMiscRepo
    search_repo: AbsSearchRepository
    storage: interfaces.AbsStorage
    users_repo: interfaces.AbsUsersRepo
