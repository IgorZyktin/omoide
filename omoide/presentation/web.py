"""Internet related tools."""

import copy
import http
from typing import Any
from typing import NoReturn
from urllib.parse import urlencode

from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import RedirectResponse

from omoide import const
from omoide import custom_logging
from omoide import exceptions as api_exceptions
from omoide import models

LOG = custom_logging.get_logger(__name__)


CODES_TO_EXCEPTIONS: dict[int, list[type[Exception]]] = {
    status.HTTP_400_BAD_REQUEST: [
        api_exceptions.InvalidInputError,
    ],
    status.HTTP_404_NOT_FOUND: [
        api_exceptions.DoesNotExistError,
    ],
    status.HTTP_409_CONFLICT: [
        api_exceptions.AlreadyExistsError,
    ],
    status.HTTP_403_FORBIDDEN: [
        api_exceptions.AccessDeniedError,
        api_exceptions.NotAllowedError,
    ],
}

EXCEPTION_TO_CODE_MAP: dict[type[Exception], int] = {
    error: code for code, errors in CODES_TO_EXCEPTIONS.items() for error in errors
}


def get_corresponding_exception_code(exc: Exception) -> int:
    """Return HTTP code that corresponds to this exception."""
    return EXCEPTION_TO_CODE_MAP.get(
        type(exc),
        http.HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def safe_template(template: str, **kwargs: str) -> str:
    """Try converting error as correct as possible."""
    message = template

    for kev, value in kwargs.items():
        message = message.replace('{' + str(kev) + '}', str(value))

    return message


def raise_from_exc(
    exc: Exception,
    language: str | None = None,
) -> NoReturn:
    """Cast exception into HTTP response."""
    LOG.exception('Failed to perform request')

    code = get_corresponding_exception_code(exc)

    if language:
        # TODO - add localization
        detail = str(exc)
    else:
        detail = str(exc)

    raise HTTPException(status_code=code, detail=detail)


def redirect_from_exc(request: Request, exc: Exception) -> RedirectResponse:
    """Return redirection from exception (do not raise)."""
    code = get_corresponding_exception_code(exc)

    match code:
        case status.HTTP_404_NOT_FOUND:
            response = RedirectResponse(request.url_for('app_not_found'))
        case status.HTTP_403_FORBIDDEN:
            response = RedirectResponse(request.url_for('app_forbidden'))
        case _:
            response = RedirectResponse(request.url_for('app_bad_request'))

    return response


class Query(BaseModel):
    """User search query."""

    raw_query: str
    tags_include: list[str]
    tags_exclude: list[str]

    def __bool__(self) -> bool:
        """Return True if query has tags to search."""
        return any((self.tags_include, self.tags_exclude))


class Aim(BaseModel):
    """Object that describes user's desired output."""

    query: Query
    order: const.ORDER_TYPE
    collections: bool
    direct: bool
    paged: bool
    page: int
    last_seen: int
    items_per_page: int

    @property
    def offset(self) -> int:
        """Return offset from start of the result block."""
        return self.items_per_page * (self.page - 1)

    def calc_total_pages(self, total_items: int) -> int:
        """Calculate how many pages we need considering this query."""
        return int(total_items / (self.items_per_page or 1))

    def using(self, **kwargs: Any) -> 'Aim':
        """Create new instance with given params."""
        values = self.model_dump()
        values.update(kwargs)
        return type(self)(**kwargs)

    def url_safe(self) -> dict:
        """Return dict that can be converted to URL."""
        params = self.model_dump()
        params['q'] = self.query.raw_query
        params.pop('query', None)
        return params


class AimWrapper:
    """Wrapper around aim object."""

    def __init__(
        self,
        aim: Aim,
    ) -> None:
        """Initialize instance."""
        self.aim = aim

    def __getattr__(self, item: str) -> Any:
        """Send all requests to the aim."""
        return getattr(self.aim, item)

    @classmethod
    def from_params(cls, params: dict, **kwargs: Any) -> 'AimWrapper':
        """Build Aim object from raw params."""
        raw_query = params.get('q', '')
        tags_include: list[str] = []
        tags_exclude: list[str] = []

        local_params = copy.deepcopy(params)
        local_params['query'] = Query(
            raw_query=raw_query,
            tags_include=tags_include,
            tags_exclude=tags_exclude,
        )

        local_params.update(kwargs)
        cls._fill_defaults(local_params)
        aim = Aim(**local_params)
        return cls(aim)

    @classmethod
    def _fill_defaults(
        cls,
        params: dict,
    ) -> None:
        """Add default values if they were not supplied."""
        # NOTE: backward compatibility for legacy endpoints
        order = params.get('order')
        ordering = params.get('ordering')

        order_final = order or ordering or 'random'
        if order_final.lower() == 'on':
            params['order'] = const.ASC
        else:
            params['order'] = const.RANDOM

        # NOTE: backward compatibility for legacy endpoints
        collections = params.get('collections')
        only_collections = params.get('only_collections')
        collections_final = collections or only_collections or 'off'

        if collections_final.lower() == 'on':
            params['collections'] = True
        else:
            params['collections'] = False

        # NOTE: backward compatibility for legacy endpoints
        direct = params.get('direct')
        nested = params.get('nested')
        direct_final = direct or nested or 'off'

        if direct_final.lower() == 'on':
            params['direct'] = True
        else:
            params['direct'] = False

        params['paged'] = cls.extract_bool(params, 'paged', False)
        params['page'] = cls.extract_int(params, 'page', 1)
        params['last_seen'] = cls.extract_int(params, 'last_seen', -1)
        params['items_per_page'] = cls.extract_int(params, 'items_per_page', 25)

        params['page'] = max(params['page'], 1)

        if params['items_per_page'] < 1:
            params['items_per_page'] = 25

    @staticmethod
    def extract_bool(
        params: dict,
        key: str,
        default: bool,
    ) -> bool:
        """Safely extract boolean value from user input."""
        value = params.get(key)

        if value is None:
            result = default
        else:
            result = value == 'on'

        return result

    @staticmethod
    def extract_int(
        params: dict,
        key: str,
        default: int,
    ) -> int:
        """Safely extract int value from user input."""
        try:
            result = int(params.get(key))  # type: ignore
        except (ValueError, TypeError):
            result = default
        return result

    def to_url(self, **kwargs: Any) -> str:
        """Convert to URL string."""
        local_params = self.aim.url_safe()
        local_params.update(kwargs)

        for key, value in local_params.items():
            if value is True:
                local_params[key] = 'on'
            elif value is False:
                local_params[key] = 'off'
            else:
                local_params[key] = str(value)

        return urlencode(local_params)

    def to_url_no_q(self, **kwargs: Any) -> str:
        """Create same url but without query."""
        kwargs['q'] = ''
        return self.to_url(**kwargs)


def _get_href(request: Request, item: models.Item) -> str:
    """Return base for HREF formation."""
    base = request.scope.get('root_path')
    prefix = str(item.uuid)[:2]
    return f'{base}/content/{{media_type}}/{item.owner_uuid}/{prefix}/{item.uuid}'


def get_content_href(request: Request, item: models.Item) -> str:
    """Return URL to the file."""
    base = _get_href(request, item)
    ext = f'.{item.content_ext}' if item.content_ext else ''
    return base.format(media_type='content') + ext


def get_preview_href(request: Request, item: models.Item) -> str:
    """Return URL to the file."""
    base = _get_href(request, item)
    ext = f'.{item.preview_ext}' if item.preview_ext else ''
    return base.format(media_type='preview') + ext


def get_thumbnail_href(request: Request, item: models.Item) -> str:
    """Return URL to the file."""
    base = _get_href(request, item)
    ext = f'.{item.thumbnail_ext}' if item.thumbnail_ext else ''
    return base.format(media_type='thumbnail') + ext
