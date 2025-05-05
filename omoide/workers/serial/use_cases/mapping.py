"""Map of name to use cases."""

from omoide.workers.serial.use_cases import permissions_use_cases
from omoide.workers.serial.use_cases import tags_use_cases
from omoide.workers.serial.use_cases import upload_use_cases

NAMES_TO_USE_CASES = {
    'rebuild_computed_tags': tags_use_cases.RebuildComputedTagsForItemUseCase,
    'rebuild_known_tags_for_all': tags_use_cases.RebuildKnownTagsForAllUseCase,
    'rebuild_known_tags_for_anon': tags_use_cases.RebuildKnownTagsForAnonUseCase,
    'rebuild_known_tags_for_user': tags_use_cases.RebuildKnownTagsForUserUseCase,
    'rebuild_permissions': permissions_use_cases.RebuildPermissionsForItemUseCase,  # noqa: E501
    'upload': upload_use_cases.UploadItemUseCase,
}
