"""Class that ties all components together."""

from dataclasses import dataclass

from omoide import interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.database.interfaces.abs_exif_repo import AbsEXIFRepo
from omoide.database.interfaces.abs_signatures_repo import AbsSignaturesRepo
from omoide.object_storage import interfaces as object_interfaces
from omoide.storage import interfaces as storage_interfaces


@dataclass
class Mediator:
    """Class that ties all components together."""

    authenticator: interfaces.AbsAuthenticator
    browse: storage_interfaces.AbsBrowseRepository
    exif: AbsEXIFRepo
    items: storage_interfaces.AbsItemsRepo
    meta: storage_interfaces.AbsMetainfoRepo
    misc: storage_interfaces.AbsMiscRepo
    search: storage_interfaces.AbsSearchRepository
    signatures: AbsSignaturesRepo
    storage: storage_interfaces.AbsStorage
    database: AbsDatabase
    users: storage_interfaces.AbsUsersRepo

    object_storage: object_interfaces.AbsObjectStorage
