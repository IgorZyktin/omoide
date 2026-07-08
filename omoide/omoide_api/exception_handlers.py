"""Global exception handler for the omoide_api FastAPI app.

Converts ``BaseOmoideError`` subclasses into ``JSONResponse`` instances so
controllers do not have to wrap every body in ``try/except``. Unknown
exceptions are left for FastAPI's default 500 path.
"""

from fastapi.responses import JSONResponse
from starlette.requests import Request

from omoide import custom_logging
from omoide import exceptions
from omoide.presentation.web import get_corresponding_exception_code

LOG = custom_logging.get_logger(__name__)


async def handle_omoide_error(request: Request, exc: Exception) -> JSONResponse:
    """Render an Omoide exception as a JSON error response."""
    _ = request
    if isinstance(exc, exceptions.AccessDeniedError):
        LOG.warning(str(exc), exc_info=exc)
    else:
        LOG.exception(str(exc), exc_info=exc)
    return JSONResponse(
        {'message': str(exc)},
        status_code=get_corresponding_exception_code(exc),
    )
