# -*- coding: utf-8 -*-
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
from uuid import UUID

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from omoide import domain
from omoide import utils
from omoide.domain import errors
from omoide.presentation import constants

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
        errors.EXIFDoesNotExist,
        errors.UserDoesNotExist,
        errors.MediaDoesNotExist,
        errors.MetainfoDoesNotExist,
    ],

    http.HTTPStatus.FORBIDDEN: [
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


def safe_template(template, **kwargs) -> str:
    """Try converting error as correct as possible."""
    message = template

    for kev, value in kwargs.items():
        try:
            message = message.replace('{' + str(kev) + '}', str(value))
        except KeyError:
            pass

    return message


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
    except KeyError as exc:
        print(exc)  # TODO: replace with logger call
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
            request.url_for('not_found') + f'?q={uuid}'
        )

    if code in (http.HTTPStatus.FORBIDDEN, http.HTTPStatus.UNAUTHORIZED) \
            and uuid is not None:
        response = RedirectResponse(
            request.url_for('unauthorized') + f'?q={uuid}'
        )

    if response is None:
        response = RedirectResponse(request.url_for('bad_request'))

    return response


def login_required(func: Callable) -> Callable:
    """Redirect anon users to login."""

    @functools.wraps(func)
    async def wrapper(
            request: Request,
            *args,
            user: domain.User,
            **kwargs,
    ):
        """Wrapper."""
        if user.is_anon():
            # TODO: try keeping original link
            return RedirectResponse(request.url_for('login'))
        return await func(request, *args, user=user, **kwargs)

    return wrapper


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


PATTERN = re.compile(r'(\s\+\s|\s-\s)')


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
