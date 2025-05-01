"""Routes related to media upload."""

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import cfg
from omoide import dependencies as dep
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_app.upload import upload_use_cases
from omoide.presentation import web

app_upload_router = fastapi.APIRouter()


@app_upload_router.get('/upload/{parent_uuid}')
async def app_upload(  # noqa: PLR0913
    request: Request,
    parent_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Upload media page."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    use_case = upload_use_cases.AppUploadUseCase(mediator)

    try:
        item, users_with_permission = await use_case.execute(user, parent_uuid)
    except Exception as exc:
        return web.redirect_from_exc(request, exc)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'endpoint': request.url_for('api_upload_item', parent_uuid=parent_uuid),
        'current_item': item,
        'users_with_permission': users_with_permission,
    }

    return templates.TemplateResponse('item_upload.html', context)
