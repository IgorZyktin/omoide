# -*- coding: utf-8 -*-
"""Preview related routes.
"""
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response

from omoide import use_cases
from omoide import utils
from omoide.domain import auth
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/preview/{uuid}')
async def app_preview(
        request: Request,
        uuid: str,
        user: auth.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppPreviewUseCase = Depends(
            dep.app_preview_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        templates: web.TemplateEngine = Depends(dep.get_templates),
        response_class: Type[Response] = HTMLResponse,
):
    """Browse contents of a single item as one object."""
    aim = aim_wrapper.aim
    valid_uuid = utils.cast_uuid(uuid)

    if valid_uuid is None:
        return web.redirect_from_error(request, errors.InvalidUUID(uuid=uuid))

    _result = await use_case.execute(policy, user, valid_uuid, aim)

    if isinstance(_result, Failure):
        return web.redirect_from_error(request, _result.error, valid_uuid)

    result = _result.value

    # TODO: put it inside use case
    tags: set[str] = set()
    tags.update(result.item.tags)

    for each in result.location.items:
        tags.update(each.item.tags)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'item': result.item,
        'metainfo': result.metainfo,
        'result': result,
        'album': infra.Album(
            sequence=result.neighbours,
            position=result.item.uuid,
            items_on_page=constants.PAGES_IN_BLOCK,
        ),
        'current_item': result.item,
        'tags': sorted(tags),
        'block_ordered': True,
        'block_nested': True,
        'block_paginated': True,
        'locate': web.get_locator(request, config.prefix_size),
    }
    return templates.TemplateResponse('preview.html', context)
