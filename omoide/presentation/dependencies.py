"""External components.
"""
import binascii
from base64 import b64decode
from functools import partial
from typing import Annotated
from typing import Optional

from databases import Database
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from omoide import constants
from omoide import infra
from omoide import use_cases
from omoide import utils
from omoide.domain import auth
from omoide.domain import interfaces
from omoide.domain.interfaces.infra.in_policy import AbsPolicy
from omoide.domain.storage.interfaces.in_rp_exif import AbsEXIFRepository
from omoide.domain.storage.interfaces.in_rp_media import AbsMediaRepository
from omoide.infra.mediator import Mediator
from omoide.presentation import app_config
from omoide.presentation import constants as app_constants
from omoide.presentation import web
from omoide.storage.repositories import asyncpg


@utils.memorize
def get_config() -> app_config.Config:
    """Get config instance."""
    return app_config.Config()


def patch_request(
        request: Request,
        config: Annotated[app_config.Config, Depends(get_config)],
) -> None:
    """Monkey-patch the request.

    Solution to a problem that should not exit.
    This must be solved using reverse proxy configuration.
    """
    if config.env != 'prod':
        return

    original_method = request.url_for
    request.url_for = partial(  # type: ignore
        web.patched_url_for,
        original_method
    )


@utils.memorize
def get_templates() -> Jinja2Templates:
    """Get templates instance."""
    templates = Jinja2Templates(directory='omoide/presentation/templates')
    templates.env.globals['zip'] = zip
    return templates


@utils.memorize
def get_db() -> Database:
    """Get database instance."""
    return Database(get_config().db_url_app.get_secret_value())


# repositories ----------------------------------------------------------------


@utils.memorize
def get_search_repo() -> interfaces.AbsSearchRepository:
    """Get repo instance."""
    return asyncpg.SearchRepository(get_db())


@utils.memorize
def get_preview_repo() -> interfaces.AbsPreviewRepository:
    """Get repo instance."""
    return asyncpg.PreviewRepository(get_db())


@utils.memorize
def get_browse_repo() -> interfaces.AbsBrowseRepository:
    """Get repo instance."""
    return asyncpg.BrowseRepository(get_db())


@utils.memorize
def get_users_repo() -> interfaces.AbsUsersRepository:
    """Get repo instance."""
    return asyncpg.UsersRepository(get_db())


@utils.memorize
def get_items_read_repo() -> interfaces.AbsItemsReadRepository:
    """Get repo instance."""
    return asyncpg.ItemsReadRepository(get_db())


@utils.memorize
def get_items_write_repo() -> interfaces.AbsItemsWriteRepository:
    """Get repo instance."""
    return asyncpg.ItemsWriteRepository(get_db())


def media_repo() -> AbsMediaRepository:
    """Get repo instance."""
    return asyncpg.MediaRepository(get_db())


def exif_repo() -> AbsEXIFRepository:
    """Get repo instance."""
    return asyncpg.EXIFRepository(get_db())


@utils.memorize
def get_metainfo_repo() -> interfaces.AbsMetainfoRepository:
    """Get repo instance."""
    return asyncpg.MetainfoRepository(get_db())


# application specific objects ------------------------------------------------


def get_aim(
        request: Request,
) -> web.AimWrapper:
    """General way of getting aim."""
    params = dict(request.query_params)
    return web.AimWrapper.from_params(
        params=params,
        items_per_page=min(app_constants.ITEMS_PER_PAGE,
                           app_constants.MAX_ITEMS_PER_PAGE),
    )


def get_credentials(
        request: Request,
) -> HTTPBasicCredentials:
    """Try extraction credentials from user request, but not trigger login."""
    authorization: Optional[str] = request.headers.get('Authorization')
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


@utils.memorize
def get_auth_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
) -> use_cases.AuthUseCase:
    """Get use case instance."""
    return use_cases.AuthUseCase(
        users_repo=users_repository,
    )


@utils.memorize
def get_authenticator() -> interfaces.AbsAuthenticator:
    """Get authenticator instance."""
    return infra.BcryptAuthenticator(
        complexity=constants.AUTH_COMPLEXITY,
    )


async def get_current_user(
        credentials: HTTPBasicCredentials = Depends(get_credentials),
        use_case: use_cases.AuthUseCase = Depends(get_auth_use_case),
        authenticator: interfaces.AbsAuthenticator = Depends(get_authenticator)
) -> auth.User:
    """Load current user or use anon user."""
    if not credentials.username or not credentials.password:
        return auth.User.new_anon()
    return await use_case.execute(credentials, authenticator)


async def get_known_user(
        credentials: HTTPBasicCredentials = Depends(get_credentials),
        use_case: use_cases.AuthUseCase = Depends(get_auth_use_case),
        authenticator: interfaces.AbsAuthenticator = Depends(get_authenticator)
) -> auth.User:
    """Load current user, raise if got anon."""
    user = None
    if credentials.username and credentials.password:
        user = await use_case.execute(credentials, authenticator)

    if user is None or user.is_not_registered:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not allowed to perform this operation',
        )

    return user


@utils.memorize
def get_policy(
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
) -> interfaces.AbsPolicy:
    """Get policy instance."""
    return infra.Policy(
        items_repo=items_read_repository,
    )


@utils.memorize
def get_mediator(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
) -> Mediator:
    """Get mediator instance."""
    return Mediator(
        users_repository=users_repository,
    )


# application related use cases -----------------------------------------------


@utils.memorize
def app_dynamic_search_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.AppDynamicSearchUseCase:
    """Get use case instance."""
    return use_cases.AppDynamicSearchUseCase(
        search_repo=search_repository,
        browse_repo=browse_repository,
    )


@utils.memorize
def app_paged_search_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.AppPagedSearchUseCase:
    """Get use case instance."""
    return use_cases.AppPagedSearchUseCase(
        search_repo=search_repository,
        browse_repo=browse_repository,
    )


@utils.memorize
def app_preview_use_case(
        preview_repository:
        interfaces.AbsPreviewRepository = Depends(get_preview_repo),
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
        metainfo_repo:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.AppPreviewUseCase:
    """Get use case instance."""
    return use_cases.AppPreviewUseCase(
        preview_repo=preview_repository,
        users_repo=users_repository,
        items_repo=items_read_repository,
        meta_repo=metainfo_repo,
    )


@utils.memorize
def app_browse_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
        metainfo_repo:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.AppBrowseUseCase:
    """Get use case instance."""
    return use_cases.AppBrowseUseCase(
        browse_repo=browse_repository,
        users_repo=users_repository,
        items_repo=items_read_repository,
        meta_repo=metainfo_repo
    )


@utils.memorize
def app_home_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.AppHomeUseCase:
    """Get use case instance."""
    return use_cases.AppHomeUseCase(
        browse_repo=browse_repository,
    )


@utils.memorize
def app_upload_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
) -> use_cases.AppUploadUseCase:
    """Get use case instance."""
    return use_cases.AppUploadUseCase(
        items_repo=items_read_repository,
        users_repo=users_repository,
    )


# app item related use cases --------------------------------------------------


@utils.memorize
def api_search_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.ApiSearchUseCase:
    """Get use case instance."""
    return use_cases.ApiSearchUseCase(
        search_repo=search_repository,
        browse_repo=browse_repository,
    )


def api_suggest_tag_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
) -> use_cases.ApiSuggestTagUseCase:
    """Get use case instance."""
    return use_cases.ApiSuggestTagUseCase(search_repo=search_repository)


@utils.memorize
def app_item_create_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
) -> use_cases.AppItemCreateUseCase:
    """Get use case instance."""
    return use_cases.AppItemCreateUseCase(
        users_repo=users_repository,
        items_repo=items_write_repository,
    )


@utils.memorize
def app_item_update_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.AppItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.AppItemUpdateUseCase(
        users_repo=users_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def app_item_delete_use_case(
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
) -> use_cases.AppItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.AppItemDeleteUseCase(
        items_repo=items_write_repository,
    )


@utils.memorize
def api_items_download_use_case(
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemsDownloadUseCase:
    """Get use case instance."""
    return use_cases.ApiItemsDownloadUseCase(
        items_repo=items_read_repository,
        metainfo_repo=metainfo_repository,
    )


# api item related use cases --------------------------------------------------


@utils.memorize
def api_item_create_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemCreateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemCreateUseCase(
        users_repo=users_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_create_bulk_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemCreateBulkUseCase:
    """Get use case instance."""
    return use_cases.ApiItemCreateBulkUseCase(
        users_repo=users_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_read_use_case(
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
) -> use_cases.ApiItemReadUseCase:
    """Get use case instance."""
    return use_cases.ApiItemReadUseCase(
        items_repo=items_write_repository,
    )


@utils.memorize
def api_item_read_by_name_use_case(
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
) -> use_cases.ApiItemReadByNameUseCase:
    """Get use case instance."""
    return use_cases.ApiItemReadByNameUseCase(
        items_repo=items_write_repository,
    )


@utils.memorize
def api_item_update_use_case(
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateUseCase(
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_update_tags_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemUpdateTagsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateTagsUseCase(
        users_repo=users_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_update_permissions_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemUpdatePermissionsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdatePermissionsUseCase(
        users_repo=users_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_item_copy_image_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        items_write_repository: Annotated[interfaces.AbsItemsWriteRepository,
                                          Depends(get_items_write_repo)],
        metainfo_repository: Annotated[interfaces.AbsMetainfoRepository,
                                       Depends(get_metainfo_repo)],
        media_repository: Annotated[AbsMediaRepository, Depends(media_repo)],
) -> use_cases.ApiCopyImageUseCase:
    """Get use case instance."""
    return use_cases.ApiCopyImageUseCase(
        policy=policy,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
        media_repo=media_repository,
    )


@utils.memorize
def api_item_update_parent_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        users_repository: Annotated[interfaces.AbsUsersRepository,
                                    Depends(get_users_repo)],
        items_write_repository: Annotated[interfaces.AbsItemsWriteRepository,
                                          Depends(get_items_write_repo)],
        metainfo_repository: Annotated[interfaces.AbsMetainfoRepository,
                                       Depends(get_metainfo_repo)],
        media_repository: Annotated[AbsMediaRepository,
                                    Depends(media_repo)],
) -> use_cases.ApiItemUpdateParentUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateParentUseCase(
        policy=policy,
        users_repo=users_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
        media_repo=media_repository,
    )


@utils.memorize
def api_item_delete_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_write_repository:
        interfaces.AbsItemsWriteRepository = Depends(get_items_write_repo),
        metainfo_repository:
        interfaces.AbsMetainfoRepository = Depends(get_metainfo_repo),
) -> use_cases.ApiItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.ApiItemDeleteUseCase(
        users_repo=users_repository,
        items_repo=items_write_repository,
        metainfo_repo=metainfo_repository,
    )


@utils.memorize
def api_browse_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.APIBrowseUseCase:
    """Get use case instance."""
    return use_cases.APIBrowseUseCase(
        browse_repo=browse_repository,
    )


# api media related use cases -------------------------------------------------


def api_create_media_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        media_repository: Annotated[AbsMediaRepository, Depends(media_repo)],
) -> use_cases.CreateMediaUseCase:
    """Get use case instance."""
    return use_cases.CreateMediaUseCase(policy=policy,
                                        media_repo=media_repository)


# api exif related use cases -------------------------------------------------


def api_create_exif_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        exif_repository: Annotated[AbsEXIFRepository, Depends(exif_repo)],
) -> use_cases.CreateEXIFUseCase:
    """Get use case instance."""
    return use_cases.CreateEXIFUseCase(policy=policy,
                                       exif_repo=exif_repository)


def api_read_exif_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        exif_repository: Annotated[AbsEXIFRepository, Depends(exif_repo)],
) -> use_cases.ReadEXIFUseCase:
    """Get use case instance."""
    return use_cases.ReadEXIFUseCase(policy=policy,
                                     exif_repo=exif_repository)


def api_update_exif_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        exif_repository: Annotated[AbsEXIFRepository, Depends(exif_repo)],
) -> use_cases.UpdateEXIFUseCase:
    """Get use case instance."""
    return use_cases.UpdateEXIFUseCase(policy=policy,
                                       exif_repo=exif_repository)


def api_delete_exif_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        exif_repository: Annotated[AbsEXIFRepository, Depends(exif_repo)],
) -> use_cases.DeleteEXIFUseCase:
    """Get use case instance."""
    return use_cases.DeleteEXIFUseCase(policy=policy,
                                       exif_repo=exif_repository)


# api metainfo related use cases ----------------------------------------------


def read_metainfo_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        metainfo_repository: Annotated[interfaces.AbsMetainfoRepository,
                                       Depends(get_metainfo_repo)],
) -> use_cases.ReadMetainfoUseCase:
    """Get use case instance."""
    return use_cases.ReadMetainfoUseCase(policy=policy,
                                         meta_repo=metainfo_repository)


def update_metainfo_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        metainfo_repository: Annotated[interfaces.AbsMetainfoRepository,
                                       Depends(get_metainfo_repo)],
) -> use_cases.UpdateMetainfoUseCase:
    """Get use case instance."""
    return use_cases.UpdateMetainfoUseCase(policy=policy,
                                           meta_repo=metainfo_repository)


# app profile related use cases -----------------------------------------------


@utils.memorize
def profile_quotas_use_case(
        users_repository:
        interfaces.AbsUsersRepository = Depends(get_users_repo),
        items_read_repository:
        interfaces.AbsItemsReadRepository = Depends(get_items_read_repo),
) -> use_cases.AppProfileQuotasUseCase:
    """Get use case instance."""
    return use_cases.AppProfileQuotasUseCase(
        users_repo=users_repository,
        items_repo=items_read_repository,
    )


@utils.memorize
def profile_new_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
) -> use_cases.APIProfileNewUseCase:
    """Get use case instance."""
    return use_cases.APIProfileNewUseCase(
        browse_repo=browse_repository,
    )


@utils.memorize
def profile_tags_use_case(
        search_repository:
        interfaces.AbsSearchRepository = Depends(get_search_repo),
) -> use_cases.AppProfileTagsUseCase:
    """Get use case instance."""
    return use_cases.AppProfileTagsUseCase(
        search_repo=search_repository,
    )
