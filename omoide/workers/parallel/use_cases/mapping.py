"""Map of name to use cases."""

from omoide.workers.parallel.use_cases import copy_use_cases
from omoide.workers.parallel.use_cases import deletion_use_cases
from omoide.workers.parallel.use_cases import download_use_cases

NAMES_TO_USE_CASES = {
    'copy': copy_use_cases.CopyUseCase,
    'download': download_use_cases.DownloadUseCase,
    'hard_delete': deletion_use_cases.HardDeleteUseCase,
    'soft_delete': deletion_use_cases.SoftDeleteUseCase,
}
