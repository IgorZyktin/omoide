"""Map of name to use cases."""

from omoide import operations
from omoide.workers.parallel.use_cases import deletion_use_cases
from omoide.workers.parallel.use_cases import download_use_cases

NAMES_TO_USE_CASES = {
    operations.DownloadMediaOp.name: download_use_cases.DownloadMediaUseCase,
    operations.HardDeleteMediaOp.name: deletion_use_cases.HardDeleteMediaUseCase,
    operations.SoftDeleteMediaOp.name: deletion_use_cases.SoftDeleteMediaUseCase,
}
