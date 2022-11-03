# -*- coding: utf-8 -*-
"""Routes related to item creation.
"""
import fastapi
from fastapi import Depends
from fastapi import Request

from omoide import domain
from omoide import utils
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/items/create')
@web.login_required
async def create_item(
        request: Request,
        parent_uuid: str = '',
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
):
    """Create item page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    if not utils.is_valid_uuid(parent_uuid):
        parent_uuid = ''

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'url': request.url_for('search'),
        'parent_uuid': parent_uuid,
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('item_create.html', context)
