# -*- coding: utf-8 -*-
"""User profile related routes.
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
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/profile')
@web.login_required
async def app_profile(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Show user home page."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
    }

    return dep.templates.TemplateResponse('profile.html', context)


@router.get('/profile/quotas')
@web.login_required
async def app_profile_quotas(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        use_case: use_cases.AppProfileQuotasUseCase = Depends(
            dep.profile_quotas_use_case),
        response_class: Type[Response] = HTMLResponse,
):
    """Show space usage stats."""
    result = await use_case.execute(user)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error)

    items_size, total_items = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'items_size': items_size,
        'total_items': total_items,
        'byte_count_to_text': utils.byte_count_to_text,
        'sep_digits': utils.sep_digits,
        'aim_wrapper': aim_wrapper,
    }

    return dep.templates.TemplateResponse('profile_quotas.html', context)


@router.get('/profile/new')
@web.login_required
async def app_profile_new(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Show recent updates."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'endpoint': request.url_for('api_profile_new'),
    }

    return dep.templates.TemplateResponse('profile_new.html', context)
