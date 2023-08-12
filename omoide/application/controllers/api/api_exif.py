"""EXIF related API operations.
"""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status

from omoide import use_cases
from omoide.domain import exceptions
from omoide.domain.application import input_models
from omoide.domain.application import output_models
from omoide.domain.core import core_models
from omoide.presentation import dependencies as dep

router = APIRouter(prefix='/api/exif')


@router.post('/{item_uuid}', status_code=status.HTTP_201_CREATED)
async def api_create_exif(
        request: Request,
        response: Response,
        item_uuid: UUID,
        in_exif: input_models.InEXIF,
        user: core_models.User = Depends(dep.get_current_user),
        use_case: use_cases.CreateEXIFUseCase = Depends(
            dep.api_create_exif_use_case),
):
    """Add EXIF data to existing item."""
    exif = core_models.EXIF(
        item_uuid=item_uuid,
        exif=in_exif.exif,
    )

    try:
        await use_case.execute(user, item_uuid, exif)
    except exceptions.AlreadyExistError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=str(exc))
    except exceptions.DoesNotExistError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(exc))
    except exceptions.ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=str(exc))

    response.headers['Location'] = str(
        request.url_for('api_create_exif', item_uuid=item_uuid)
    )

    return {}


@router.get('/{item_uuid}', status_code=status.HTTP_200_OK)
async def api_read_exif(
        item_uuid: UUID,
        user: core_models.User = Depends(dep.get_current_user),
        use_case: use_cases.ReadEXIFUseCase = Depends(
            dep.api_read_exif_use_case),
):
    """Read EXIF data for existing item."""
    try:
        result = await use_case.execute(user, item_uuid)
    except exceptions.DoesNotExistError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(exc))
    except exceptions.ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=str(exc))

    return output_models.OutEXIF(
        item_uuid=result.item_uuid,
        exif=result.exif,
    )


@router.put('/{item_uuid}', status_code=status.HTTP_202_ACCEPTED)
async def api_update_exif(
        item_uuid: UUID,
        in_exif: input_models.InEXIF,
        user: core_models.User = Depends(dep.get_current_user),
        use_case: use_cases.UpdateEXIFUseCase = Depends(
            dep.api_update_exif_use_case),
):
    """Update EXIF data for existing item."""
    exif = core_models.EXIF(
        item_uuid=item_uuid,
        exif=in_exif.exif,
    )

    try:
        await use_case.execute(user, item_uuid, exif)
    except exceptions.DoesNotExistError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(exc))
    except exceptions.ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=str(exc))

    return {}


@router.delete('/{item_uuid}', status_code=status.HTTP_202_ACCEPTED)
async def api_delete_exif(
        item_uuid: UUID,
        user: core_models.User = Depends(dep.get_current_user),
        use_case: use_cases.DeleteEXIFUseCase = Depends(
            dep.api_delete_exif_use_case),
):
    """Delete EXIF data from exising item."""
    try:
        await use_case.execute(user, item_uuid)
    except exceptions.DoesNotExistError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(exc))
    except exceptions.ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=str(exc))

    return {}
