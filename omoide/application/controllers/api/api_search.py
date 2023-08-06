"""Search related API operations.
"""
from fastapi import APIRouter
from fastapi import Depends

from omoide import use_cases
from omoide.domain import errors
from omoide.domain.application import app_constants
from omoide.domain.application import output_models
from omoide.domain.core import core_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/search')


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
