"""Class that ties all components together."""
from dataclasses import dataclass

from omoide.domain import interfaces
from omoide.storage import interfaces as storage_interfaces


@dataclass()
class Mediator:
    """Class that ties all components together."""
    authenticator: interfaces.AbsAuthenticator
    browse_repo: storage_interfaces.AbsBrowseRepository
    exif_repo: storage_interfaces.AbsEXIFRepository
    items_repo: storage_interfaces.AbsItemsRepo
    media_repo: storage_interfaces.AbsMediaRepository
    meta_repo: storage_interfaces.AbsMetainfoRepo
    misc_repo: storage_interfaces.AbsMiscRepo
    search_repo: storage_interfaces.AbsSearchRepository
    storage: storage_interfaces.AbsStorage
    users_repo: storage_interfaces.AbsUsersRepo
