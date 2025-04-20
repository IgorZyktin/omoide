"""Map of name to use cases."""

from omoide import operations
from omoide.workers.parallel.use_cases import deletion_use_cases

NAMES_TO_USE_CASES = {
    operations.SoftDeleteMediaOp.name: deletion_use_cases.SoftDeleteMediaUseCase,
    operations.HardDeleteMediaOp.name: deletion_use_cases.HardDeleteMediaUseCase,
}
