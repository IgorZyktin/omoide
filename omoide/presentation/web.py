"""Internet related tools."""
import copy
import http
from typing import Any
from typing import NoReturn
from typing import Optional
from typing import Type
from urllib.parse import urlencode
from uuid import UUID

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from omoide import const
from omoide import domain
from omoide import exceptions as api_exceptions
from omoide.domain import errors
from omoide import custom_logging
from omoide.presentation import constants

LOG = custom_logging.get_logger(__name__)

# TODO - rewrite to base classes
CODES_TO_ERRORS: dict[int, list[Type[errors.Error]]] = {
    # not supposed to be used, but just in case
    http.HTTPStatus.INTERNAL_SERVER_ERROR: [
        errors.Error,
    ],

    http.HTTPStatus.BAD_REQUEST: [
        errors.NoUUID,
        errors.InvalidUUID,
    ],

    http.HTTPStatus.NOT_FOUND: [
        errors.ItemDoesNotExist,
        errors.UserDoesNotExist,
    ],

    http.HTTPStatus.FORBIDDEN: [
        errors.AuthenticationRequired,
        errors.ItemRequiresAccess,
        errors.ItemModificationByAnon,
    ]
}

ERROR_TO_CODE_MAP: dict[Type[errors.Error], int] = {
    error: code
    for code, errors in CODES_TO_ERRORS.items()
    for error in errors
}

CODES_TO_EXCEPTIONS: dict[int, list[Type[Exception]]] = {
    http.HTTPStatus.BAD_REQUEST: [
        api_exceptions.InvalidInputError,
    ],

    http.HTTPStatus.NOT_FOUND: [
        api_exceptions.DoesNotExistError,
    ],

    http.HTTPStatus.FORBIDDEN: [
        api_exceptions.AccessDeniedError,
    ]
}

EXCEPTION_TO_CODE_MAP: dict[Type[Exception], int] = {
    error: code
    for code, errors in CODES_TO_EXCEPTIONS.items()
    for error in errors
}


def get_corresponding_error_code(error: errors.Error) -> int:
    """Return HTTP code that corresponds to this error."""
    return ERROR_TO_CODE_MAP.get(
        type(error),
        http.HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def get_corresponding_exception_code(exc: Exception) -> int:
    """Return HTTP code that corresponds to this exception."""
    return EXCEPTION_TO_CODE_MAP.get(
        type(exc),
        http.HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def safe_template(template: str, **kwargs) -> str:
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
    code = get_corresponding_exception_code(exc)

    if language:
        # TODO - add localization
        detail = str(exc)
    else:
        detail = str(exc)

    raise HTTPException(status_code=code, detail=detail)


def raise_from_error(
    error: errors.Error,
    language: Optional[str] = None,
) -> NoReturn:
    """Cast domain level Error into HTTP response."""
    code = get_corresponding_error_code(error)

    # TODO - add actual language so errors could be translated
    assert language is None

    try:
        message = error.template.format(**error.kwargs)
    except KeyError:
        LOG.exception('Failed to raise from error')
        message = safe_template(error.template, **error.kwargs)

    raise HTTPException(status_code=code, detail=message)


def redirect_from_error(
    request: Request,
    error: errors.Error,
    uuid: Optional[UUID] = None,
) -> RedirectResponse:
    """Return appropriate response."""
    code = get_corresponding_error_code(error)
    response = None

    if code == http.HTTPStatus.BAD_REQUEST:
        response = RedirectResponse(request.url_for('bad_request'))

    elif code == http.HTTPStatus.NOT_FOUND and uuid is not None:
        response = RedirectResponse(
            str(request.url_for('not_found')) + f'?q={uuid}'
        )

    if (code in (http.HTTPStatus.FORBIDDEN, http.HTTPStatus.UNAUTHORIZED)
            and uuid is not None):
        response = RedirectResponse(
            str(request.url_for('unauthorized')) + f'?q={uuid}'
        )

    if response is None:
        response = RedirectResponse(request.url_for('bad_request'))

    return response


class AimWrapper:
    """Wrapper around aim object."""

    def __init__(
        self,
        aim: domain.Aim,
    ) -> None:
        """Initialize instance."""
        self.aim = aim

    def __getattr__(self, item: str) -> Any:
        """Send all requests to the aim."""
        return getattr(self.aim, item)

    @classmethod
    def from_params(
        cls,
        params: dict,
        **kwargs,
    ) -> 'AimWrapper':
        """Build Aim object from raw params."""
        raw_query = params.get('q', '')
        tags_include, tags_exclude = [], []

        local_params = copy.deepcopy(params)
        local_params['query'] = domain.Query(
            raw_query=raw_query,
            tags_include=tags_include,
            tags_exclude=tags_exclude,
        )

        local_params.update(kwargs)
        cls._fill_defaults(local_params)
        aim = domain.Aim(**local_params)
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
        params['items_per_page'] = cls.extract_int(params, 'items_per_page',
                                                   constants.ITEMS_PER_PAGE)

        if params['page'] < 1:
            params['page'] = 1

        if params['items_per_page'] < 1:
            params['items_per_page'] = constants.ITEMS_PER_PAGE

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

    def to_url(self, **kwargs) -> str:
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

    def to_url_no_q(self, **kwargs) -> str:
        """Same as to url but without query."""
        kwargs['q'] = ''
        return self.to_url(**kwargs)


def _get_href(request: Request, item: domain.Item) -> str:
    """Return base for HREF formation."""
    base = request.scope.get('root_path')
    prefix = str(item.uuid)[:2]
    return (
        f'{base}/content/{{media_type}}/{item.owner_uuid}/{prefix}/{item.uuid}'
    )


def get_content_href(request: Request, item: domain.Item) -> str:
    """Return URL to the file."""
    base = _get_href(request, item)
    ext = f'.{item.content_ext}' if item.content_ext else ''
    return base.format(media_type='content') + ext


def get_preview_href(request: Request, item: domain.Item) -> str:
    """Return URL to the file."""
    base = _get_href(request, item)
    ext = f'.{item.preview_ext}' if item.preview_ext else ''
    return base.format(media_type='preview') + ext


def get_thumbnail_href(request: Request, item: domain.Item) -> str:
    """Return URL to the file."""
    base = _get_href(request, item)
    ext = f'.{item.thumbnail_ext}' if item.thumbnail_ext else ''
    return base.format(media_type='thumbnail') + ext
