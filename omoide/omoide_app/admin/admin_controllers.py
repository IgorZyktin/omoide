"""Admin page."""

from typing import Annotated

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import cfg
from omoide import custom_logging
from omoide import dependencies as dep
from omoide import models
from omoide.presentation import web

LOG = custom_logging.get_logger(__name__)

app_admin_router = fastapi.APIRouter()


@app_admin_router.get('/admin')
async def app_admin(
    request: Request,
    admin: Annotated[models.User, Depends(dep.get_current_user)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Create item page."""
    if not admin.is_admin:
        return RedirectResponse(request.url_for('app_forbidden'))

    context = {
        'request': request,
        'config': config,
        'user': admin,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'create_user_endpoint': request.url_for('api_create_user'),
        'rebuild_computed_tags_endpoint': request.url_for('api_action_rebuild_computed_tags'),
    }

    return templates.TemplateResponse('admin.html', context)
