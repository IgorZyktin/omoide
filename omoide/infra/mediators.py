"""Class that ties all components together."""

from dataclasses import dataclass

from omoide.database import interfaces as database_interfaces
from omoide.infra import interfaces as infra_interfaces
from omoide.object_storage import interfaces as object_interfaces


@dataclass
class Mediator:
    """Class that ties all components together."""

    authenticator: infra_interfaces.AbsAuthenticator
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


@dataclass(frozen=True)
class EXIFMediator:
    """Class that ties all components together."""

    authenticator: infra_interfaces.AbsAuthenticator
    database: database_interfaces.AbsDatabase
    exif: database_interfaces.AbsEXIFRepo
    items: database_interfaces.AbsItemsRepo


@dataclass(frozen=True)
class MetainfoMediator:
    """Class that ties all components together."""

    authenticator: infra_interfaces.AbsAuthenticator
    database: database_interfaces.AbsDatabase
    items: database_interfaces.AbsItemsRepo
    meta: database_interfaces.AbsMetaRepo


@dataclass(frozen=True)
class SearchMediator:
    """Class that ties all components together."""

    browse: database_interfaces.AbsBrowseRepo
    database: database_interfaces.AbsDatabase
    search: database_interfaces.AbsSearchRepo
    tags: database_interfaces.AbsTagsRepo
    users: database_interfaces.AbsUsersRepo


@dataclass(frozen=True)
class HomeMediator:
    """Class that ties all components together."""

    database: database_interfaces.AbsDatabase
    search: database_interfaces.AbsSearchRepo
    users: database_interfaces.AbsUsersRepo
