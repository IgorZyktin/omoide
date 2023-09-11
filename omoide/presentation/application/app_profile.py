"""User profile related routes.
"""
from typing import Annotated
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import domain
from omoide import use_cases
from omoide import utils
from omoide.domain import errors
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/profile')
async def app_profile(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Show user home page."""
    if user.is_not_registered or user.uuid is None:
        error = errors.AuthenticationRequired()
        return web.redirect_from_error(request, error)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
    }
    return templates.TemplateResponse('profile.html', context)


@router.get('/profile/quotas')
async def app_profile_quotas(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        use_case: use_cases.AppProfileQuotasUseCase = Depends(
            dep.profile_quotas_use_case),
        response_class: Type[Response] = HTMLResponse,
):
    """Show space usage stats."""
    result = await use_case.execute(user)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error)

    items_size, total_items, total_collections = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'items_size': items_size,
        'total_items': total_items,
        'total_collections': total_collections,
        'byte_count_to_text': utils.byte_count_to_text,
        'sep_digits': utils.sep_digits,
        'aim_wrapper': aim_wrapper,
    }

    return templates.TemplateResponse('profile_quotas.html', context)


@router.get('/profile/new')
async def app_profile_new(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Show recent updates."""
    if user.is_not_registered or user.uuid is None:
        error = errors.AuthenticationRequired()
        return web.redirect_from_error(request, error)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'endpoint': request.url_for('api_profile_new'),
    }
    return templates.TemplateResponse('profile_new.html', context)


@router.get('/profile/tags')
async def app_profile_tags(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        use_case: use_cases.AppProfileTagsUseCase = Depends(
            dep.profile_tags_use_case),
        response_class: Type[Response] = HTMLResponse,
):
    """Show know tags."""
    if user.is_not_registered or user.uuid is None:
        error = errors.AuthenticationRequired()
        return web.redirect_from_error(request, error)

    result = await use_case.execute(user)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error)

    known_tags = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'known_tags': known_tags,
        'sep_digits': utils.sep_digits,
        'aim_wrapper': aim_wrapper,
    }

    return templates.TemplateResponse('profile_tags.html', context)
