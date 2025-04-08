"""Map of name to use cases."""

from omoide import models
from omoide.workers.serial.use_cases import permissions_use_cases
from omoide.workers.serial.use_cases import tags_use_cases

NAMES_TO_USE_CASES = {
    models.RebuildKnownTagsForAnonRequest.name: {
        'request_type': models.RebuildKnownTagsForAnonRequest,
        'use_case_type': tags_use_cases.RebuildKnownTagsForAnonUseCase,
    },
    models.RebuildKnownTagsForUserRequest.name: {
        'request_type': models.RebuildKnownTagsForUserRequest,
        'use_case_type': tags_use_cases.RebuildKnownTagsForUserUseCase,
    },
    models.RebuildKnownTagsForAllRequest.name: {
        'request_type': models.RebuildKnownTagsForAllRequest,
        'use_case_type': tags_use_cases.RebuildKnownTagsForAllUseCase,
    },
    models.RebuildComputedTagsForItemRequest.name: {
        'request_type': models.RebuildComputedTagsForItemRequest,
        'use_case_type': tags_use_cases.RebuildComputedTagsForItemUseCase,
    },
    models.RebuildPermissionsForItemRequest.name: {
        'request_type': models.RebuildPermissionsForItemRequest,
        'use_case_type': permissions_use_cases.RebuildPermissionsForItemUseCase,
    },
}
