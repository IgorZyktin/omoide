"""EXIF related API operations.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import status

from omoide import use_cases
from omoide.application import web
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
        user: Annotated[core_models.User, Depends(dep.get_known_user)],
        use_case: Annotated[use_cases.CreateEXIFUseCase,
                            Depends(dep.api_create_exif_use_case)],
):
    """Add EXIF data to existing item."""
    exif = core_models.EXIF(
        item_uuid=item_uuid,
        exif=in_exif.exif,
    )

    await web.run(use_case.execute, user, item_uuid, exif)

    response.headers['Location'] = str(
        request.url_for('api_read_exif', item_uuid=item_uuid)
    )

    return {}


@router.get('/{item_uuid}', status_code=status.HTTP_200_OK)
async def api_read_exif(
        item_uuid: UUID,
        user: Annotated[core_models.User, Depends(dep.get_current_user)],
        use_case: Annotated[use_cases.ReadEXIFUseCase,
                            Depends(dep.api_read_exif_use_case)],
):
    """Read EXIF data for existing item."""
    result = await web.run(use_case.execute, user, item_uuid)
    return output_models.OutEXIF(
        item_uuid=result.item_uuid,
        exif=result.exif,
    )


@router.put('/{item_uuid}', status_code=status.HTTP_202_ACCEPTED)
async def api_update_exif(
        item_uuid: UUID,
        in_exif: input_models.InEXIF,
        user: Annotated[core_models.User, Depends(dep.get_known_user)],
        use_case: Annotated[use_cases.UpdateEXIFUseCase,
                            Depends(dep.api_update_exif_use_case)],
):
    """Update EXIF data for existing item."""
    exif = core_models.EXIF(
        item_uuid=item_uuid,
        exif=in_exif.exif,
    )

    await web.run(use_case.execute, user, item_uuid, exif)
    return {}


@router.delete('/{item_uuid}', status_code=status.HTTP_202_ACCEPTED)
async def api_delete_exif(
        item_uuid: UUID,
        user: Annotated[core_models.User, Depends(dep.get_known_user)],
        use_case: Annotated[use_cases.DeleteEXIFUseCase,
                            Depends(dep.api_delete_exif_use_case)],
):
    """Delete EXIF data from exising item."""
    await web.run(use_case.execute, user, item_uuid)
    return {}
