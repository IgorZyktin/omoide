"""Global exception handler for the omoide_app FastAPI app.

Converts ``BaseOmoideError`` subclasses into a ``RedirectResponse`` to the
matching error page (forbidden / not_found / bad_request) so controllers
do not have to wrap every body in ``try/except``.
"""

from starlette.requests import Request
from starlette.responses import RedirectResponse

from omoide.presentation.web import redirect_from_exc


async def handle_omoide_error(request: Request, exc: Exception) -> RedirectResponse:
    """Render an Omoide exception as a redirect to the matching error page."""
    return redirect_from_exc(request, exc)
