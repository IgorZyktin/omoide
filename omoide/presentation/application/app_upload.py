"""Routes related to media upload."""
from typing import Annotated
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import models
from omoide import use_cases
from omoide import utils
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/upload/{uuid}')
async def app_upload(
        request: Request,
        uuid: str,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppUploadUseCase = Depends(
            dep.app_upload_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Upload media page."""
    valid_uuid = utils.cast_uuid(uuid)

    if valid_uuid is None:
        return web.redirect_from_error(request, errors.InvalidUUID(uuid=uuid))

    _result = await use_case.execute(policy, user, valid_uuid)

    if isinstance(_result, Failure):
        return web.redirect_from_error(request, _result.error, valid_uuid)

    item, permissions = _result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'item': item,
        'permissions': permissions,
        'locate': web.get_locator(request, config.prefix_size),
    }

    return templates.TemplateResponse('upload.html', context)
