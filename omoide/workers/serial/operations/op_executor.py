"""Operations executor."""

import abc
from typing import Any
from typing import Generic
from typing import TypeVar

from omoide import exceptions
from omoide.serial_operations import SerialOperation

_ALL_SERIAL_OPERATIONS_EXECUTORS: dict[
    str,
    type['SerialOperationExecutor'],
] = {}

ConfigT = TypeVar('ConfigT')
MediatorT = TypeVar('MediatorT')


class SerialOperationExecutor(Generic[ConfigT, MediatorT], abc.ABC):
    """Generic executor."""

    operation: SerialOperation

    def __init__(
        self,
        operation: SerialOperation,
        config: ConfigT,
        mediator: MediatorT,
    ) -> None:
        """Initialize instance."""
        self.operation = operation
        self.config = config
        self.mediator = mediator

    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        """Store descendant."""
        super().__init_subclass__(*args, **kwargs)
        key = cls.__annotations__['operation'].name
        _ALL_SERIAL_OPERATIONS_EXECUTORS[key] = cls

    @staticmethod
    def from_operation(
        operation: SerialOperation,
        config: ConfigT,
        mediator: MediatorT,
    ) -> 'SerialOperationExecutor':
        """Create specific instance type."""
        executor_type = _ALL_SERIAL_OPERATIONS_EXECUTORS.get(operation.name)

        if executor_type is None:
            raise exceptions.UnknownSerialOperationError(name=operation.name)

        return executor_type(operation, config, mediator)

    @abc.abstractmethod
    async def execute(self) -> None:
        """Perform workload."""
