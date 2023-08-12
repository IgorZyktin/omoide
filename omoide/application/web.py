"""Internet related tools.
"""
from typing import Awaitable
from typing import Callable
from typing import ParamSpec
from typing import TypeVar

from fastapi import HTTPException
from fastapi import status

from omoide.domain import exceptions
from omoide.infra import custom_logging

LOG = custom_logging.get_logger(__name__)

RT = TypeVar('RT')  # return type
P = ParamSpec('P')


async def run(
        executable: Callable[P, Awaitable[RT]],
        *args: P.args,
        **kwargs: P.kwargs,
) -> RT:
    """Execute use case and wrap exceptions."""
    try:
        result = await executable(*args, **kwargs)
    except exceptions.AlreadyExistError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except exceptions.DoesNotExistError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except exceptions.ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except Exception:
        LOG.exception(
            'Failed to execute %(name)s '
            'with args %(args)s and kwargs %(kwargs)s',
            {
                'name': executable.__name__,
                'args': args,
                'kwargs': kwargs,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to perform request',
        )
    return result
