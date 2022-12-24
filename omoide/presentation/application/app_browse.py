# -*- coding: utf-8 -*-
"""Browse related routes.
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


@router.get('/browse/{uuid}')
async def app_browse(
        request: Request,
        uuid: str,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppBrowseUseCase = Depends(
            dep.app_browse_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Browse contents of a single item as collection."""
    aim = aim_wrapper.aim
    valid_uuid = utils.cast_uuid(uuid)

    if valid_uuid is None:
        return web.redirect_from_error(request, errors.InvalidUUID(uuid=uuid))

    _result = await use_case.execute(policy, user, valid_uuid, aim)

    if isinstance(_result, Failure):
        return web.redirect_from_error(request, _result.error, valid_uuid)

    result = _result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'uuid': uuid,
        'aim_wrapper': aim_wrapper,
        'location': result.location,
        'api_url': request.url_for('api_browse', uuid=uuid),
        'result': result,
        'current_item': result.item,
        'locate': web.get_locator(request, config.prefix_size),
    }

    if result.paginated:
        template = 'browse_paginated.html'
        paginator = infra.Paginator(
            page=aim.page,
            items_per_page=aim.items_per_page,
            total_items=result.total_items,
            pages_in_block=constants.PAGES_IN_BLOCK,
        )
        context['paginator'] = paginator
    else:
        template = 'browse_dynamic.html'

    return dep.get_templates().TemplateResponse(template, context)
