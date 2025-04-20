"""Map of name to use cases."""

from omoide import operations
from omoide.workers.serial.use_cases import permissions_use_cases
from omoide.workers.serial.use_cases import tags_use_cases
from omoide.workers.serial.use_cases import introduce_use_cases

NAMES_TO_USE_CASES = {
    operations.IntroduceItemOp.name: introduce_use_cases.IntroduceItemUseCase,
    operations.RebuildComputedTagsForItemOp.name: tags_use_cases.RebuildComputedTagsForItemUseCase,
    operations.RebuildKnownTagsForAllOp.name: tags_use_cases.RebuildKnownTagsForAllUseCase,
    operations.RebuildKnownTagsForAnonOp.name: tags_use_cases.RebuildKnownTagsForAnonUseCase,
    operations.RebuildKnownTagsForUserOp.name: tags_use_cases.RebuildKnownTagsForUserUseCase,
    operations.RebuildPermissionsForItemOp.name: permissions_use_cases.RebuildPermissionsForItemUseCase,  # noqa: E501
}
