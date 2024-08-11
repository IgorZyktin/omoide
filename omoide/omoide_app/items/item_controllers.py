"""Routes for item-related pages."""

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import custom_logging
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_app.items import item_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

LOG = custom_logging.get_logger(__name__)

app_items_router = fastapi.APIRouter()


@app_items_router.get('/create/{parent_uuid}')
async def app_create_item(
    request: Request,
    parent_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,
):
    """Create item page."""
    if user.is_anon:
        return RedirectResponse(request.url_for('forbidden'))

    use_case = item_use_cases.AppCreateItemUseCase(mediator)

    try:
        parent, users_with_permission = await use_case.execute(
            user=user,
            parent_uuid=parent_uuid,
        )
    except Exception as exc:
        web.redirect_from_exc(request, exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'endpoint': request.url_for('api_create_item'),
        'current_item': parent,
        'parent_item': parent,
        'users_with_permission': users_with_permission,
    }

    return templates.TemplateResponse('create_item.html', context)
