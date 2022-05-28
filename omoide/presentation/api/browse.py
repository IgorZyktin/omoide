# -*- coding: utf-8 -*-
"""Browse page related API operations.
"""
import fastapi

from omoide import domain, use_cases
from omoide.presentation import dependencies as dep, utils, infra

router = fastapi.APIRouter()


@router.get('/api/browse/{uuid}')
async def api_browse(
        request: fastapi.Request,
        uuid: str,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.APIBrowseUseCase = fastapi.Depends(
            dep.api_browse_use_case),
):
    """Return portion of items for browse template."""
    valid_uuid = infra.parse.cast_uuid(uuid)
    aim = domain.aim_from_params(dict(request.query_params))
    items = await use_case.execute(user, valid_uuid, aim)
    return utils.to_simple_items(request, items)
