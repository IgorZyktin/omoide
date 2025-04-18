"""Map of name to use cases."""

from omoide import models
from omoide.workers.parallel.use_cases import use_cases

NAMES_TO_USE_CASES = {
    models.SoftDeleteMediaRequest.name: {
        'request_type': models.SoftDeleteMediaRequest,
        'use_case_type': use_cases.SoftDeleteMediaUseCase,
    },
}
