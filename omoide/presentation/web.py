"""Internet related tools.
"""
import copy
import functools
import http
import re
from typing import Any
from typing import Callable
from typing import NoReturn
from typing import Optional
from typing import Type
from urllib.parse import urlencode
from uuid import UUID

from fastapi import HTTPException
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import RedirectResponse

from omoide import domain
from omoide import utils
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.infra import custom_logging
from omoide.presentation import constants
from omoide.utils import maybe_str

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
        errors.MetainfoDoesNotExist,
    ],

    http.HTTPStatus.FORBIDDEN: [
        errors.AuthenticationRequired,
        errors.ItemRequiresAccess,
        errors.ItemNoDeleteForRoot,
        errors.ItemModificationByAnon,
    ]
}

ERROR_TO_CODE_MAP: dict[Type[errors.Error], int] = {
    error: code
    for code, errors in CODES_TO_ERRORS.items()
    for error in errors
}


def get_corresponding_error_code(error: errors.Error) -> int:
    """Return HTTP code that corresponds to this error."""
    return ERROR_TO_CODE_MAP.get(
        type(error),
        http.HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def safe_template(template: str, **kwargs) -> str:
    """Try converting error as correct as possible."""
    message = template

    for kev, value in kwargs.items():
        message = message.replace('{' + str(kev) + '}', str(value))

    return message


def to_simple_type(something: Any) -> None | str:
    """Convert one item."""
    if something is None:
        return None

    return str(something)


def serialize(
    payload: dict[str, Any],
) -> dict[str, None | str]:
    """Convert dictionary to a web-compatible format."""
    return {
        key: to_simple_type(value)
        for key, value in payload.items()
    }


def raise_from_exc(exc: Exception) -> NoReturn:
    """Cast exception into HTTP response."""
    error = errors.Error(
        template='{error_type}: {error_message}',
        error_type=type(exc).__name__,
        error_message=str(exc),
    )
    raise_from_error(error)


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

    if code in (http.HTTPStatus.FORBIDDEN, http.HTTPStatus.UNAUTHORIZED) \
            and uuid is not None:
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
        tags_include, tags_exclude = parse_tags(raw_query)

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
        params['ordered'] = cls.extract_bool(params, 'ordered', False)
        params['nested'] = cls.extract_bool(params, 'nested', False)
        params['paged'] = cls.extract_bool(params, 'paged', False)
        params['page'] = cls.extract_int(params, 'page', 1)
        params['last_seen'] = cls.extract_int(params, 'last_seen', -1)
        params['items_per_page'] = cls.extract_int(params, 'items_per_page',
                                                   constants.ITEMS_PER_PAGE)

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


PATTERN = re.compile(r'(\s+\+\s+|\s+-\s+)')


def parse_tags(raw_query: str) -> tuple[list[str], list[str]]:
    """Split  user query into tags."""
    tags_include = []
    tags_exclude = []

    parts = PATTERN.split(raw_query)
    clean_parts = [x.strip() for x in parts if x.strip()]

    if not clean_parts:
        return [], []

    if clean_parts[0] not in ('+', '-'):
        clean_parts.insert(0, '+')

    for operator, tag in utils.group_to_size(clean_parts):
        tag = str(tag).lower()
        if operator == '+':
            tags_include.append(tag)
        else:
            tags_exclude.append(tag)

    return tags_include, tags_exclude


def url_join(*args: str) -> str:
    """Join url components."""
    segments = [
        x.strip().strip('/')
        for x in args
        if x.strip().strip('/')
    ]

    if not segments:
        return '/'
    return '/'.join(segments)


class Locator(interfaces.AbsLocator):
    """Helper object that generates links for items."""

    def __init__(
            self,
            request: Request,
            item: domain.Item,
            prefix_size: int,
    ) -> None:
        """Initialize instance."""
        super().__init__(item, prefix_size)
        self.request = request
        self.url_for = request.url_for

    @functools.cached_property
    def head(self) -> str:
        """Return starting common part of the path."""
        return url_join(
            maybe_str(self.url_for('app_home')),
            'content',
        )

    @functools.cached_property
    def body(self) -> str:
        """Return middle common part of the path."""
        return url_join(
            str(self.item.owner_uuid),
            str(self.item.uuid)[:self.prefix_size],
        )

    @functools.cached_property
    def content(self) -> str:
        """Return URL to the content."""
        return url_join(
            self.head,
            'content',
            self.body,
            self.content_filename
        )

    @functools.cached_property
    def preview(self) -> str:
        """Return URL to the preview."""
        return url_join(
            self.head,
            'preview',
            self.body,
            self.preview_filename
        )

    @functools.cached_property
    def thumbnail(self) -> str:
        """Return URL to the thumbnail."""
        return url_join(
            self.head,
            'thumbnail',
            self.body,
            self.thumbnail_filename
        )


def get_locator(
        request: Request,
        prefix_size: int,
) -> Callable[[domain.Item], Locator]:
    """Make new locator."""
    return lambda item: Locator(
        request=request,
        prefix_size=prefix_size,
        item=item,
    )


def items_to_dict(
        request: Request,
        items: list[domain.Item],
        names: list[Optional[str]],
        prefix_size: int,
) -> list[domain.SimpleItem]:
    """Convert items to JSON compatible dicts."""
    assert len(items) == len(names)
    empty_thumbnail = request.url_for('static', path='empty.png')

    simple_items: list[domain.SimpleItem] = []

    for name, item in zip(names, items):
        if item.is_collection:
            href = request.url_for('app_browse', uuid=item.uuid)
        else:
            href = request.url_for('app_preview', uuid=item.uuid)

        if item.thumbnail_ext is None:
            thumbnail = empty_thumbnail
        else:
            locator = Locator(
                request=request,
                prefix_size=prefix_size,
                item=item,
            )
            thumbnail = locator.thumbnail  # type: ignore

        simple_item = domain.SimpleItem(
            uuid=str(item.uuid),
            parent_name=name,
            name=item.name,
            is_collection=item.is_collection,
            href=str(href),
            number=item.number,
            thumbnail=thumbnail,  # type: ignore
        )
        simple_items.append(simple_item)

    return simple_items


def patched_url_for(
        url_for: Callable[[str, ...], URL],  # type: ignore
        name: str,
        **path_params: Any,
) -> str:
    """Sanitized version with scheme altering."""
    url = str(url_for(name, **path_params))  # type: ignore

    # noinspection HttpUrlsUsage
    if url.startswith('http://www'):
        new_url = 'https://' + url[10:]
        LOG.warning('Replacing {} to {} (got name {} with path_params {})',
                    url, new_url, name, path_params)
        url = new_url

    elif url.startswith('http://'):
        url = 'https://' + url[7:]

    return url
