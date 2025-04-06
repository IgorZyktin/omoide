"""Dependencies."""

from base64 import b64decode
import binascii
import functools
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
import python_utilz as pu
from starlette.requests import Request

from omoide import cfg
from omoide import const
from omoide import infra
from omoide import models
from omoide.database.implementations import impl_sqlalchemy
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.infra.interfaces import AbsAuthenticator
from omoide.infra.interfaces import AbsPolicy
from omoide.infra.mediator import Mediator
from omoide.object_storage import interfaces as object_interfaces
from omoide.object_storage.implementations.file_server import FileObjectStorageServer
from omoide.object_storage.implementations.object_storage_web import ObjectStorageWeb
from omoide.omoide_app.auth.auth_use_cases import LoginUserUseCase
from omoide.presentation import web


@functools.cache
def get_config() -> cfg.Config:
    """Get config instance."""
    return pu.from_env(cfg.Config, env_prefix='omoide_app')


@functools.cache
def get_templates() -> Jinja2Templates:
    """Get templates instance."""
    templates = Jinja2Templates(directory='omoide/presentation/templates')
    templates.env.globals['zip'] = zip
    templates.env.globals['version'] = str(const.FRONTEND_VERSION)

    config = get_config()
    object_storage = ObjectStorageWeb(prefix_size=config.prefix_size)
    templates.env.globals['get_content_url'] = object_storage.get_content_url
    templates.env.globals['get_preview_url'] = object_storage.get_preview_url
    templates.env.globals['get_thumbnail_href'] = object_storage.get_thumbnail_url

    templates.env.globals['human_readable_size'] = pu.human_readable_size
    templates.env.globals['sep_digits'] = pu.sep_digits
    templates.env.globals['Status'] = models.Status
    return templates


@functools.cache
def get_database() -> impl_sqlalchemy.SqlalchemyDatabase:
    """Get database instance."""
    config = get_config()
    return impl_sqlalchemy.SqlalchemyDatabase(
        db_url=config.db_url.get_secret_value(),
        echo=False,
    )


# application specific objects ------------------------------------------------


def get_aim(request: Request) -> web.AimWrapper:
    """General way of getting aim."""
    params = dict(request.query_params)
    return web.AimWrapper.from_params(
        params=params,
        items_per_page=25,
    )


def get_credentials(request: Request) -> HTTPBasicCredentials:
    """Extract credentials from user request, but do not trigger login."""
    authorization: str | None = request.headers.get('Authorization')
    anon = HTTPBasicCredentials(username='', password='')

    if authorization:
        scheme, _, param = authorization.partition(' ')

        if scheme.lower() == 'basic':
            try:
                data = b64decode(param).decode('ascii')
            except (ValueError, UnicodeDecodeError, binascii.Error):
                return anon

            username, separator, password = data.partition(':')

            if not separator:
                return anon

            return HTTPBasicCredentials(username=username, password=password)

    return anon


def get_authenticator() -> AbsAuthenticator:
    """Get authenticator instance."""
    return infra.BcryptAuthenticator()


def get_policy() -> AbsPolicy:
    """Get policy instance."""
    return infra.Policy()


@functools.cache
def get_object_storage(
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> object_interfaces.AbsObjectStorage:
    """Get policy instance."""
    config = get_config()
    return FileObjectStorageServer(
        database=database,
        media=impl_sqlalchemy.MediaRepo(),
        prefix_size=config.prefix_size,
    )


@functools.cache
def get_mediator(
    authenticator: Annotated[AbsAuthenticator, Depends(get_authenticator)],
    policy: Annotated[AbsPolicy, Depends(get_policy)],
    object_storage: Annotated[object_interfaces.AbsObjectStorage, Depends(get_object_storage)],
    database: Annotated[AbsDatabase, Depends(get_database)],
) -> Mediator:
    """Get mediator instance."""
    return Mediator(
        authenticator=authenticator,
        policy=policy,
        database=database,
        browse=impl_sqlalchemy.BrowseRepo(),
        exif=impl_sqlalchemy.EXIFRepo(),
        items=impl_sqlalchemy.ItemsRepo(),
        meta=impl_sqlalchemy.MetaRepo(),
        misc=impl_sqlalchemy.MiscRepo(),
        search=impl_sqlalchemy.SearchRepo(),
        signatures=impl_sqlalchemy.SignaturesRepo(),
        tags=impl_sqlalchemy.TagsRepo(),
        users=impl_sqlalchemy.UsersRepo(),
        object_storage=object_storage,
    )


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(get_credentials)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> models.User:
    """Return current user or create anon."""
    use_case = LoginUserUseCase(mediator)
    if not credentials.username or not credentials.password:
        return models.User.new_anon()
    return await use_case.execute(credentials.username, credentials.password)


async def get_known_user(
    current_user: Annotated[models.User, Depends(get_current_user)],
) -> models.User:
    """Return current user, raise if user is anon."""
    if current_user.is_not_anon:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='You must be registered to do this',
    )


async def get_admin_user(
    current_user: Annotated[models.User, Depends(get_known_user)],
) -> models.User:
    """Return current user, raise if user is not admin."""
    if current_user.is_admin:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='You must be an admin to do this',
    )
