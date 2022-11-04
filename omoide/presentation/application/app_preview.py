# -*- coding: utf-8 -*-
"""Preview related routes.
"""
import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse

from omoide import domain
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
async def preview(
        request: Request,
        uuid: str,
        user: auth.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppPreviewUseCase = Depends(
            dep.app_preview_use_case),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Browse contents of a single item as one object."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)
    aim = domain.aim_from_params(dict(request.query_params))

    valid_uuid = utils.cast_uuid(uuid)

    if valid_uuid is None:
        _result = Failure(errors.InvalidUUID(uuid=uuid))
    else:
        _result = await use_case.execute(policy, user, valid_uuid, details)

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
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
        'item': result.item,
        'result': result,
        'album': infra.Album(
            sequence=result.neighbours,
            position=result.item.uuid,
            items_on_page=constants.PAGES_IN_BLOCK,  # TODO: move to details
        ),
        'current_item': result.item,
        'tags': sorted(tags),
    }
    return dep.templates.TemplateResponse('preview.html', context)
