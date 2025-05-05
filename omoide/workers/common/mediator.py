"""Class that ties all components together."""

from dataclasses import dataclass

from omoide.database.interfaces import abs_database
from omoide.database.interfaces import abs_exif_repo
from omoide.database.interfaces import abs_items_repo
from omoide.database.interfaces import abs_meta_repo
from omoide.database.interfaces import abs_misc_repo
from omoide.database.interfaces import abs_signatures_repo
from omoide.database.interfaces import abs_tags_repo
from omoide.database.interfaces import abs_users_repo
from omoide.database.interfaces import abs_worker_repo
from omoide.object_storage.implementations.file_client import FileObjectStorageClient


@dataclass
class WorkerMediator:
    """Class that ties all components together."""

    database: abs_database.AbsDatabase
    exif: abs_exif_repo.AbsEXIFRepo
    items: abs_items_repo.AbsItemsRepo
    meta: abs_meta_repo.AbsMetaRepo
    misc: abs_misc_repo.AbsMiscRepo
    object_storage: FileObjectStorageClient
    signatures: abs_signatures_repo.AbsSignaturesRepo
    tags: abs_tags_repo.AbsTagsRepo
    users: abs_users_repo.AbsUsersRepo
    workers: abs_worker_repo.AbsWorkersRepo

    stopping: bool = False
