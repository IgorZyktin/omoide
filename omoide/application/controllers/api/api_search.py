"""Search related API operations.
"""
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends

from omoide import use_cases
from omoide.application import web
from omoide.domain.application import app_constants
from omoide.domain.application import output_models
from omoide.domain.core import core_models
from omoide.infra import custom_logging
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/search')

LOG = custom_logging.get_logger(__name__)


@router.get('/suggest')
async def api_suggest_tag(
        user: Annotated[core_models.User, Depends(dep.get_current_user)],
        use_case: Annotated[use_cases.ApiSuggestTagUseCase,
                            Depends(dep.api_suggest_tag_use_case)],
        text: str = '',
        response_model=output_models.OutAutocomplete,
):
    """Return tags for autocompletion in search field."""
    variants: list[str] = []

    if len(text) > 1:
        result = await web.run(
            use_case.execute, user, text, app_constants.AUTOCOMPLETE_VARIANTS)
        variants = [guess_result.tag for guess_result in result]

    return output_models.OutAutocomplete(variants=variants)
