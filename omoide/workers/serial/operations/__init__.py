"""Global namespace for all operations."""

from omoide import const
from omoide import exceptions
from omoide import models
from omoide.workers.common.mediator import WorkerMediator
from omoide.workers.serial.cfg import Config
from omoide.workers.serial.operations.base import SerialOperationImplementation
from omoide.workers.serial.operations.op_rebuild_known_tags import RebuildKnownTagsAllOperation
from omoide.workers.serial.operations.op_rebuild_known_tags import RebuildKnownTagsAnonOperation
from omoide.workers.serial.operations.op_rebuild_known_tags import (
    RebuildKnownTagsUserOperation,
)
from omoide.workers.serial.operations.op_rebuild_permissions import RebuildItemPermissionsOperation
from omoide.workers.serial.operations.op_rebuild_tags import RebuildItemTagsOperation

NAME_MAP = {
    const.AllSerialOperations.REBUILD_KNOWN_TAGS_ANON: RebuildKnownTagsAnonOperation,
    const.AllSerialOperations.REBUILD_KNOWN_TAGS_USER: RebuildKnownTagsUserOperation,
    const.AllSerialOperations.REBUILD_KNOWN_TAGS_ALL: RebuildKnownTagsAllOperation,
    const.AllSerialOperations.REBUILD_ITEM_TAGS: RebuildItemTagsOperation,
    const.AllSerialOperations.REBUILD_ITEM_PERMISSIONS: RebuildItemPermissionsOperation,
}


def get_implementation(
    operation: models.SerialOperation,
    config: Config,
    mediator: WorkerMediator,
) -> SerialOperationImplementation:
    """Return specific version of operation."""
    operation_type = NAME_MAP.get(const.AllSerialOperations(operation.name))

    if operation_type is None:
        raise exceptions.UnknownSerialOperationError(name=operation.name)

    return operation_type(operation, config, mediator)
