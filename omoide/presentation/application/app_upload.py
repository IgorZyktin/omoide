# -*- coding: utf-8 -*-
"""Routes related to media upload.
"""
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response

from omoide import domain
from omoide import use_cases
from omoide import utils
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/upload/{uuid}')
@web.login_required
async def app_upload(
        request: Request,
        uuid: str,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppUploadUseCase = Depends(
            dep.app_upload_use_case),
        config: Config = Depends(dep.config),
        response_class: Type[Response] = HTMLResponse,
):
    """Upload media page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

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
        'aim': aim,
        'url': request.url_for('app_search'),
        'item': item,
        'permissions': permissions,
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('upload.html', context)
