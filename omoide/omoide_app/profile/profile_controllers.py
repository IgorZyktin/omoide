"""User profile page related routes."""

from typing import Annotated
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_app.profile import profile_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

LOG = custom_logging.get_logger(__name__)

app_profile_router = fastapi.APIRouter()


@app_profile_router.get('/profile/usage')
async def app_profile_usage(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: Type[Response] = HTMLResponse,
):
    """Show space usage stats."""
    if user.is_anon:
        return RedirectResponse(request.url_for('forbidden'))

    use_case = profile_use_cases.AppProfileUsageUseCase(mediator)

    try:
        size, total_items, total_collections = await use_case.execute(user)
    # TODO - manage redirects automatically
    except exceptions.NotAllowedError:
        LOG.exception('Access denied')
        return RedirectResponse(request.url_for('forbidden'))
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    context = {
        'request': request,
        'config': config,
        'user': user,
        'size': size,
        'total_items': total_items,
        'total_collections': total_collections,
        'aim_wrapper': aim_wrapper,
    }

    return templates.TemplateResponse('profile_usage.html', context)


@app_profile_router.get('/profile/tags')
async def app_profile_tags(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: Type[Response] = HTMLResponse,
):
    """Show know tags."""
    if user.is_anon:
        return RedirectResponse(request.url_for('forbidden'))

    use_case = profile_use_cases.AppProfileTagsUseCase(mediator)

    try:
        known_tags = await use_case.execute(user)
    # TODO - manage redirects automatically
    except exceptions.NotAllowedError:
        LOG.exception('Access denied')
        return RedirectResponse(request.url_for('forbidden'))
    except Exception as exc:
        return web.raise_from_exc(exc)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'known_tags': known_tags,
        'aim_wrapper': aim_wrapper,
    }

    return templates.TemplateResponse('profile_tags.html', context)


@app_profile_router.get('/profile/new')
async def app_profile_new(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: Type[Response] = HTMLResponse,
):
    """Show recent updates."""
    if user.is_anon:
        return RedirectResponse(request.url_for('forbidden'))

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'endpoint': request.url_for('api_get_recent_updates'),
    }
    return templates.TemplateResponse('profile_new.html', context)
