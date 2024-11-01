"""Class that ties all components together."""

from dataclasses import dataclass

from omoide.database import interfaces as database_interfaces
from omoide.infra import interfaces as infra_interfaces
from omoide.object_storage import interfaces as object_interfaces


@dataclass
class Mediator:
    """Class that ties all components together."""

    authenticator: infra_interfaces.AbsAuthenticator
    policy: infra_interfaces.AbsPolicy
    database: database_interfaces.AbsDatabase

    browse: database_interfaces.AbsBrowseRepo
    exif: database_interfaces.AbsEXIFRepo
    items: database_interfaces.AbsItemsRepo
    meta: database_interfaces.AbsMetaRepo
    misc: database_interfaces.AbsMiscRepo
    search: database_interfaces.AbsSearchRepo
    signatures: database_interfaces.AbsSignaturesRepo
    tags: database_interfaces.AbsTagsRepo
    users: database_interfaces.AbsUsersRepo

    object_storage: object_interfaces.AbsObjectStorage
