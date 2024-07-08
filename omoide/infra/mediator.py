"""Class that ties all components together."""
from dataclasses import dataclass

# FIXME - make uniform import path
from omoide.domain.interfaces import AbsItemsRepo
from omoide.domain.interfaces import AbsSearchRepository
from omoide.storage.interfaces.base_storage_interfaces import AbsStorage
from omoide.storage.interfaces.in_repositories.in_rp_exif import (
    AbsEXIFRepository
)
from omoide.storage.interfaces.in_repositories.in_rp_users import AbsUsersRepo


@dataclass()
class Mediator:
    """Class that ties all components together."""
    exif_repo: AbsEXIFRepository
    items_repo: AbsItemsRepo
    search_repo: AbsSearchRepository
    storage: AbsStorage
    users_repo: AbsUsersRepo
