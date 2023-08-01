"""Search related API operations.
"""
from fastapi import APIRouter
from fastapi import Depends
from starlette.requests import Request

from omoide import domain
from omoide import use_cases
from omoide.domain import errors
from omoide.domain.application import app_constants
from omoide.domain.application import output_models
from omoide.domain.core import core_models
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


@router.get('/suggest')
async def api_suggest_tag(
        user: core_models.User = Depends(dep.get_current_user),
        text: str = '',
        use_case: use_cases.ApiSuggestTagUseCase = Depends(
            dep.api_suggest_tag_use_case),
        response_model=output_models.OutAutocomplete,
):
    """Return tags for autocompletion in search field."""
    variants: list[str] = []

    if len(text) > 1:
        result = await use_case.execute(
            user=user,
            user_input=text,
            limit=app_constants.AUTOCOMPLETE_VARIANTS,
        )

        if not isinstance(result, errors.Error):
            variants = [guess_result.tag for guess_result in result]

    return output_models.OutAutocomplete(variants=variants)
