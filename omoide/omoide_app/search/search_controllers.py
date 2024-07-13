"""Search related operations."""
import time
from typing import Annotated
from typing import Type

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_app.search import search_use_cases
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

api_search_router = APIRouter(prefix='/api/search')
app_search_router = APIRouter(prefix='/search')


@api_search_router.get('')
async def api_search(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
):
    """Return portion of random items."""
    use_case = search_use_cases.ApiSearchUseCase(mediator)
    items, names = await use_case.execute(user, aim_wrapper.aim)
    return web.items_to_dict(request, items, names)


@app_search_router.get('')
async def app_search(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    config: Annotated[Config, Depends(dep.get_config)],
    response_class: Type[Response] = HTMLResponse,
):
    """Main page of the application."""
    start = time.perf_counter()
    aim = aim_wrapper.aim

    use_case_dynamic = search_use_cases.AppDynamicSearchUseCase(mediator)
    matching_items = await use_case_dynamic.execute(user, aim_wrapper.aim)

    if aim.paged:
        template = 'search_paged.html'
        use_case_paged = search_use_cases.AppPagedSearchUseCase(mediator)
        items, names = await use_case_paged.execute(user, aim)
        paginator = infra.Paginator(
            page=aim.page,
            items_per_page=aim.items_per_page,
            total_items=matching_items,
            pages_in_block=constants.PAGES_IN_BLOCK,
        )

    else:
        items = []
        names = []
        template = 'search_dynamic.html'
        paginator = None

    delta = time.perf_counter() - start

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'paginator': paginator,
        'items': items,
        'names': names,
        'matching_items': utils.sep_digits(matching_items),
        'delta': f'{delta:0.3f}',
        'endpoint': request.url_for('api_search'),
    }

    return templates.TemplateResponse(template, context)
