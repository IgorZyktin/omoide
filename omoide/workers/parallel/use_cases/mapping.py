"""Map of name to use cases."""

from omoide.workers.parallel.use_cases import copy_use_cases

NAMES_TO_USE_CASES = {
    'copy': copy_use_cases.CopyUseCase,
}
