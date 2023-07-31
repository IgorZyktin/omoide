"""EXIF related API operations.
"""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from starlette import status

from omoide import domain
from omoide import use_cases
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.domain.application import input_models
from omoide.domain.application import output_models
from omoide.domain.core import core_models
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/exif')


@router.post('/{item_uuid}', status_code=status.HTTP_201_CREATED)
async def api_create_exif(
        request: Request,
        response: Response,
        item_uuid: UUID,
        in_exif: input_models.InEXIF,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.CreateEXIFUseCase = Depends(
            dep.create_exif_use_case),
):
    """Add EXIF data to existing item."""
    exif = core_models.EXIF(
        item_uuid=item_uuid,
        exif=in_exif.exif,
    )

    result = await use_case.execute(policy, user, item_uuid, exif)

    if isinstance(result, errors.Error):
        web.raise_from_error(result)

    response.headers['Location'] = str(
        request.url_for('api_create_exif', item_uuid=item_uuid)
    )

    return {}


@router.get('/{item_uuid}', status_code=status.HTTP_200_OK)
async def api_read_exif(
        item_uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ReadEXIFUseCase = Depends(
            dep.read_exif_use_case),
):
    """Read EXIF data for existing item."""
    result = await use_case.execute(policy, user, item_uuid)

    if isinstance(result, errors.Error):
        web.raise_from_error(result)

    return output_models.OutEXIF(
        item_uuid=result.item_uuid,
        exif=result.exif,
    )


@router.put('/{item_uuid}', status_code=status.HTTP_202_ACCEPTED)
async def api_update_exif(
        item_uuid: UUID,
        in_exif: input_models.InEXIF,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.UpdateEXIFUseCase = Depends(
            dep.update_exif_use_case),
):
    """Update EXIF data for existing item."""
    exif = core_models.EXIF(
        item_uuid=item_uuid,
        exif=in_exif.exif,
    )

    result = await use_case.execute(policy, user, item_uuid, exif)

    if isinstance(result, errors.Error):
        web.raise_from_error(result)

    return {}


@router.delete('/{item_uuid}', status_code=status.HTTP_202_ACCEPTED)
async def api_delete_exif(
        item_uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.DeleteEXIFUseCase = Depends(
            dep.delete_exif_use_case),
):
    """Delete EXIF data from exising item."""
    result = await use_case.execute(policy, user, item_uuid)

    if isinstance(result, errors.Error):
        web.raise_from_error(result)

    return {}
