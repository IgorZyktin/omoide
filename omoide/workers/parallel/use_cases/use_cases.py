"""Use cases for parallel operations."""

from omoide import custom_logging
from omoide import models
from omoide.workers.parallel.use_cases.base_use_case import BaseParallelWorkerUseCase

LOG = custom_logging.get_logger(__name__)


class SoftDeleteMediaUseCase(BaseParallelWorkerUseCase):
    """Use case for soft deleting media."""

    def execute(self, request: models.SoftDeleteMediaRequest) -> None:
        """Perform workload."""
        print(request)
        # old_path = path / filename
        # target_path = old_path
        #
        # while old_path.exists():
        #     new_filename = self.make_new_filename(filename)
        #     new_path = path / new_filename
        #
        #     if new_path.exists():
        #         LOG.debug('New name is already taken: {}', new_path)
        #         continue
        #
        #     LOG.debug('Renaming {} to {}', old_path, new_filename)
        #     old_path.replace(new_path)
        #     break
        #
        # LOG.debug('Saving {}', target_path)
        # target_path.write_bytes(content)
        # return target_path
