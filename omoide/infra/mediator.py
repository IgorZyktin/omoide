"""Class that ties all components together."""
from dataclasses import dataclass

# FIXME - make uniform import path
from omoide.domain.interfaces import AbsAuthenticator
from omoide.domain.interfaces import AbsItemsRepo
from omoide.domain.interfaces import AbsMediaRepository
from omoide.domain.interfaces import AbsSearchRepository
from omoide.storage import interfaces


@dataclass()
class Mediator:
    """Class that ties all components together."""
    authenticator: AbsAuthenticator
    exif_repo: interfaces.AbsEXIFRepository
    items_repo: AbsItemsRepo
    media_repo: AbsMediaRepository
    meta_repo: interfaces.AbsMetainfoRepo
    misc_repo: interfaces.AbsMiscRepo
    search_repo: AbsSearchRepository
    storage: interfaces.AbsStorage
    users_repo: interfaces.AbsUsersRepo
