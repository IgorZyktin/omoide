"""User profile page related routes."""

from typing import Annotated

import fastapi
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import cfg
from omoide import custom_logging
from omoide import dependencies as dep
from omoide import limits
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_app.profile import profile_use_cases
from omoide.presentation import web

LOG = custom_logging.get_logger(__name__)

app_profile_router = fastapi.APIRouter()


@app_profile_router.get('/profile')
async def app_profile(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Show user profile page."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'block_direct': True,
        'block_ordered': True,
        'block_collections': True,
        'block_paginated': True,
        'url': request.url_for('app_search'),
    }
    return templates.TemplateResponse('profile.html', context)


@app_profile_router.get('/profile/usage')
async def app_profile_usage(  # noqa: PLR0913
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Show space usage stats."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    use_case = profile_use_cases.AppProfileUsageUseCase(mediator)

    try:
        size, total_items, total_collections = await use_case.execute(user)
    except Exception as exc:
        return web.redirect_from_exc(request, exc)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'size': size,
        'total_items': total_items,
        'total_collections': total_collections,
        'block_direct': True,
        'block_ordered': True,
        'block_collections': True,
        'block_paginated': True,
        'aim_wrapper': aim_wrapper,
    }

    return templates.TemplateResponse('profile_usage.html', context)


@app_profile_router.get('/profile/tags')
async def app_profile_tags(  # noqa: PLR0913
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Show know tags."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    use_case = profile_use_cases.AppProfileTagsUseCase(mediator)

    try:
        known_tags = await use_case.execute(user)
    except Exception as exc:
        return web.redirect_from_exc(request, exc)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'known_tags': known_tags,
        'aim_wrapper': aim_wrapper,
        'block_direct': True,
        'block_ordered': True,
        'block_collections': True,
        'block_paginated': True,
    }

    return templates.TemplateResponse('profile_tags.html', context)


@app_profile_router.get('/profile/new')
async def app_profile_new(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Show recent updates."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'block_direct': True,
        'block_ordered': True,
        'block_collections': False,
        'block_paginated': True,
        'endpoint': request.url_for('api_get_recent_updates'),
    }
    return templates.TemplateResponse('profile_new.html', context)


@app_profile_router.get('/profile/duplicates')
async def app_profile_duplicates(  # noqa: PLR0913 Too many arguments in function definition
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    item_uuid: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT)] = limits.DEF_LIMIT,
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Show duplicated items."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    use_case = profile_use_cases.AppProfileDuplicatesUseCase(mediator)

    try:
        item, duplicates = await use_case.execute(user, item_uuid, limit)
    except Exception as exc:
        return web.redirect_from_exc(request, exc)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'duplicates': duplicates,
        'aim_wrapper': aim_wrapper,
        'item': item,
        'block_direct': True,
        'block_ordered': True,
        'block_collections': True,
        'block_paginated': True,
    }

    return templates.TemplateResponse('profile_duplicates.html', context)
