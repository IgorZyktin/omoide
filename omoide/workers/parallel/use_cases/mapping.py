"""Map of name to use cases."""

from omoide import operations
from omoide.workers.parallel.use_cases import use_cases

NAMES_TO_USE_CASES = {
    operations.SoftDeleteMediaOp.name: use_cases.SoftDeleteMediaUseCase,
}
