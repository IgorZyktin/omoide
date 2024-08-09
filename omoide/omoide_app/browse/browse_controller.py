"""Browse related routes."""

from typing import Annotated
from typing import Type
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import custom_logging
from omoide import exceptions
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_app.browse import browse_use_cases
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

LOG = custom_logging.get_logger(__name__)

app_browse_router = fastapi.APIRouter(prefix='/browse')


@app_browse_router.get('/{item_uuid}')
async def app_browse(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    item_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Config = Depends(dep.get_config),
    aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
    response_class: Type[Response] = HTMLResponse,
):
    """Browse contents of a single item."""
    if not aim_wrapper.aim.paged:
        use_case_dynamic = browse_use_cases.AppBrowseDynamicUseCase(mediator)

        try:
            parents, item, metainfo = await use_case_dynamic.execute(
                user=user,
                item_uuid=item_uuid,
            )
        # TODO - manage redirects automatically
        except exceptions.DoesNotExistError:
            LOG.exception('Not found')
            return RedirectResponse(request.url_for('not_found'))
        except exceptions.NotAllowedError:
            LOG.exception('Access denied')
            return RedirectResponse(request.url_for('forbidden'))
        except Exception as exc:
            web.raise_from_exc(exc)
            raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

        context = {
            'request': request,
            'config': config,
            'user': user,
            'aim_wrapper': aim_wrapper,
            'endpoint': request.url_for('api_browse', item_uuid=item_uuid),
            'parents': parents,
            'current_item': item,
            'metainfo': metainfo,
        }

        return templates.TemplateResponse('browse_dynamic.html', context)

    use_case_paged = browse_use_cases.AppBrowsePagedUseCase(mediator)

    try:
        result = await use_case_paged.execute(
            user=user,
            item_uuid=item_uuid,
            aim=aim_wrapper.aim,
        )
    # TODO - manage redirects automatically
    except exceptions.DoesNotExistError:
        LOG.exception('Not found')
        return RedirectResponse(request.url_for('not_found'))
    except exceptions.NotAllowedError:
        LOG.exception('Access denied')
        return RedirectResponse(request.url_for('forbidden'))
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    paginator = infra.Paginator(
        page=aim_wrapper.aim.page,
        items_per_page=aim_wrapper.aim.items_per_page,
        total_items=result.total_items,
        pages_in_block=constants.PAGES_IN_BLOCK,
    )

    context = {
        'request': request,
        'config': config,
        'user': user,
        'names': result.names,
        'aim_wrapper': aim_wrapper,
        'endpoint': request.url_for('api_browse', item_uuid=item_uuid),
        'result': result,
        'current_item': result.item,
        'parents': result.parents,
        'metainfo': result.metainfo,
        'paginator': paginator,
        'block_collections': True,
    }

    return templates.TemplateResponse('browse_paged.html', context)
