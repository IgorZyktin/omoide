"""EXIF related API operations.
"""
from fastapi import APIRouter
from fastapi import Depends
from starlette import status

from omoide import domain
from omoide import use_cases
from omoide.domain import interfaces
from omoide.domain.application import input_models
from omoide.infra import impl
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/exif')


@router.post('/{item_uuid}', status_code=status.HTTP_201_CREATED)
async def api_create_exif(
        item_uuid: impl.UUID,
        in_exif: input_models.InEXIF,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.CreateEXIFUseCase = Depends(
            dep.create_exif_use_case),
):
    """Create EXIF."""
    result = await use_case.execute(policy, user, item_uuid, in_exif)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.get('/{item_uuid}')
async def api_read_exif(
        item_uuid: impl.UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ReadEXIFUseCase = Depends(
            dep.read_exif_use_case),
):
    """Read EXIF entry."""
    result = await use_case.execute(policy, user, item_uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return result.value


@router.put('/{item_uuid}')
async def api_update_exif(
        item_uuid: impl.UUID,
        in_exif: input_models.InEXIF,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.UpdateEXIFUseCase = Depends(
            dep.update_exif_use_case),
):
    """Update EXIF."""
    result = await use_case.execute(policy, user, item_uuid, in_exif)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.delete('/{item_uuid}', status_code=status.HTTP_202_ACCEPTED)
async def api_delete_exif(
        item_uuid: impl.UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.DeleteEXIFUseCase = Depends(
            dep.delete_exif_use_case),
):
    """Delete EXIF."""
    result = await use_case.execute(policy, user, item_uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}
