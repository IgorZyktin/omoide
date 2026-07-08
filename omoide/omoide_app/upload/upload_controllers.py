"""Routes related to media upload."""

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import cfg
from omoide import dependencies as dep
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.omoide_app.upload import upload_use_cases
from omoide.presentation import web

app_upload_router = fastapi.APIRouter()


@app_upload_router.get('/upload/{parent_uuid}', response_model=None)
async def app_upload(  # noqa: PLR0913
    request: Request,
    parent_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
) -> HTMLResponse:
    """Upload media page."""
    use_case = upload_use_cases.AppUploadUseCase(database, items_repo, users_repo)
    result = await use_case.execute(user, parent_uuid)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'current_item': result.item,
        'users_with_permission': result.users_with_permission,
    }

    return templates.TemplateResponse(request, 'item_upload.html', context)
