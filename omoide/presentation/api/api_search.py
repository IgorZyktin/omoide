"""Search related API operations.
"""
from fastapi import APIRouter
from fastapi import Depends
from starlette.requests import Request

from omoide import domain
from omoide import use_cases
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = APIRouter(prefix='/api/search')


@router.get('')
async def api_search(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.ApiSearchUseCase = Depends(
            dep.api_search_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        templates: web.TemplateEngine = Depends(dep.get_templates),
):
    """Return portion of random items."""
    result = await use_case.execute(user, aim_wrapper.aim)

    simple_items: list[domain.SimpleItem] = []
    if isinstance(result, Failure):
        return simple_items

    items, names = result.value
    simple_items = web.items_to_dict(
        request, templates, items, names, config.prefix_size)

    return simple_items
