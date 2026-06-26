"""Admin pages."""

from typing import Annotated

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from omoide.database import interfaces as db_interfaces
from omoide import cfg, exceptions
from omoide import custom_logging
from omoide import dependencies as dep
from omoide import models
from omoide.database.interfaces import AbsDatabase
from omoide.omoide_app.admin import admin_use_cases
from omoide.presentation import web

LOG = custom_logging.get_logger(__name__)

app_admin_router = fastapi.APIRouter()


@app_admin_router.get('/admin')
async def app_admin(
    request: Request,
    admin: Annotated[models.User, Depends(dep.get_current_user)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
) -> HTMLResponse:
    """Create item page."""
    if not admin.is_admin:
        msg = 'Only admins can access this page'
        raise exceptions.AccessDeniedError(msg)

    context = {
        'request': request,
        'config': config,
        'user': admin,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
    }

    return templates.TemplateResponse(request, 'admin.html', context)


@app_admin_router.get('/admin/resource_usage')
async def app_admin_resource_usage(
    request: Request,
    admin: Annotated[models.User, Depends(dep.get_current_user)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    database: Annotated[AbsDatabase, Depends(dep.get_database)],
    users_repo: Annotated[db_interfaces.AbsUsersRepo, Depends(dep.get_users_repo)],
    meta_repo: Annotated[db_interfaces.AbsMetaRepo, Depends(dep.get_meta_repo)],
) -> HTMLResponse:
    """Show resource usage for every user."""
    if not admin.is_admin:
        msg = 'Only admins can access this page'
        raise exceptions.AccessDeniedError(msg)

    use_case = admin_use_cases.ShowResourceUsageUseCase(
        database, users_repo, meta_repo
    )
    resource_usage = await use_case.execute(admin)

    context = {
        'request': request,
        'config': config,
        'user': admin,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'resource_usage': resource_usage,
    }

    return templates.TemplateResponse(
        request, 'admin_resource_usage.html', context
    )
