"""Dependencies."""
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

from omoide import const
from omoide import infra
from omoide import models
from omoide import use_cases
from omoide import utils
from omoide.domain import interfaces
from omoide.domain.interfaces import AbsBrowseRepository
from omoide.domain.interfaces import AbsItemsRepo
from omoide.domain.interfaces import AbsPreviewRepository
from omoide.domain.interfaces import AbsSearchRepository
from omoide.domain.interfaces.infra.in_policy import AbsPolicy
from omoide.domain.storage.interfaces.in_rp_media import AbsMediaRepository
from omoide.infra.mediator import Mediator
from omoide.presentation import app_config
from omoide.presentation import constants as app_constants
from omoide.presentation import web
from omoide.storage import interfaces as st_interfaces
from omoide.storage.asyncpg_storage import AsyncpgStorage
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
    templates.env.globals['version'] = const.VERSION
    return templates


@utils.memorize
def get_db() -> Database:
    """Get database instance."""
    return Database(get_config().db_url_app.get_secret_value())


@utils.memorize
def get_storage() -> st_interfaces.AbsStorage:
    """Get storage instance."""
    return AsyncpgStorage(get_db())


# repositories ----------------------------------------------------------------


@utils.memorize
def get_search_repo() -> AbsSearchRepository:
    """Get repo instance."""
    return asyncpg.SearchRepository(get_db())


@utils.memorize
def get_preview_repo() -> AbsPreviewRepository:
    """Get repo instance."""
    return asyncpg.PreviewRepository(get_db())


@utils.memorize
def get_browse_repo() -> AbsBrowseRepository:
    """Get repo instance."""
    return asyncpg.BrowseRepository(get_db())


@utils.memorize
def get_users_repo() -> st_interfaces.AbsUsersRepo:
    """Get repo instance."""
    return asyncpg.UsersRepo(get_db())


@utils.memorize
def get_items_repo() -> AbsItemsRepo:
    """Get repo instance."""
    return asyncpg.ItemsRepo(get_db())


@utils.memorize
def media_repo() -> AbsMediaRepository:
    """Get repo instance."""
    return asyncpg.MediaRepository(get_db())


@utils.memorize
def get_exif_repo() -> st_interfaces.AbsEXIFRepository:
    """Get repo instance."""
    return asyncpg.EXIFRepository(get_db())


@utils.memorize
def get_misc_repo() -> st_interfaces.AbsMiscRepo:
    """Get repo instance."""
    return asyncpg.MiscRepo(get_db())


@utils.memorize
def get_metainfo_repo() -> st_interfaces.AbsMetainfoRepo:
    """Get repo instance."""
    return asyncpg.MetainfoRepo(get_db())


# application specific objects ------------------------------------------------


def get_aim(request: Request) -> web.AimWrapper:
    """General way of getting aim."""
    params = dict(request.query_params)
    return web.AimWrapper.from_params(
        params=params,
        items_per_page=min(app_constants.ITEMS_PER_PAGE,
                           app_constants.MAX_ITEMS_PER_PAGE),
    )


def get_credentials(request: Request) -> HTTPBasicCredentials:
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
    users_repo: Annotated[st_interfaces.AbsUsersRepo, Depends(get_users_repo)],
) -> use_cases.AuthUseCase:
    """Get use case instance."""
    return use_cases.AuthUseCase(users_repo=users_repo)


@utils.memorize
def get_authenticator() -> interfaces.AbsAuthenticator:
    """Get authenticator instance."""
    return infra.BcryptAuthenticator(
        complexity=const.AUTH_COMPLEXITY,
    )


async def get_current_user(
        credentials: HTTPBasicCredentials = Depends(get_credentials),
        use_case: use_cases.AuthUseCase = Depends(get_auth_use_case),
        authenticator: interfaces.AbsAuthenticator = Depends(get_authenticator)
) -> models.User:
    """Load current user or use anon user."""
    if not credentials.username or not credentials.password:
        return models.User.new_anon()
    return await use_case.execute(credentials, authenticator)


async def get_known_user(
        credentials: HTTPBasicCredentials = Depends(get_credentials),
        use_case: use_cases.AuthUseCase = Depends(get_auth_use_case),
        authenticator: interfaces.AbsAuthenticator = Depends(get_authenticator)
) -> models.User:
    """Load current user, raise if got anon."""
    user = None
    if credentials.username and credentials.password:
        user = await use_case.execute(credentials, authenticator)

    if user is None or user.is_anon:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not allowed to perform this operation',
        )

    return user


@utils.memorize
def get_policy(
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> interfaces.AbsPolicy:
    """Get policy instance."""
    return infra.Policy(items_repo=items_repo)


@utils.memorize
def get_mediator(
    authenticator: Annotated[interfaces.AbsAuthenticator,
                             Depends(get_authenticator)],
    exif_repo: Annotated[st_interfaces.AbsEXIFRepository,
                         Depends(get_exif_repo)],
    items_repo: Annotated[AbsItemsRepo, Depends(get_items_repo)],
    meta_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[st_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
    search_repo: Annotated[AbsSearchRepository, Depends(get_search_repo)],
    storage: Annotated[st_interfaces.AbsStorage, Depends(get_storage)],
    users_repo: Annotated[st_interfaces.AbsUsersRepo, Depends(get_users_repo)],
) -> Mediator:
    """Get mediator instance."""
    return Mediator(
        authenticator=authenticator,
        exif_repo=exif_repo,
        items_repo=items_repo,
        meta_repo=meta_repo,
        misc_repo=misc_repo,
        search_repo=search_repo,
        storage=storage,
        users_repo=users_repo,
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
        users_repo: st_interfaces.AbsUsersRepo = Depends(get_users_repo),
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
        meta_repo: st_interfaces.AbsMetainfoRepo = Depends(get_metainfo_repo),
) -> use_cases.AppPreviewUseCase:
    """Get use case instance."""
    return use_cases.AppPreviewUseCase(
        preview_repo=preview_repository,
        users_repo=users_repo,
        items_repo=items_repo,
        meta_repo=meta_repo,
    )


@utils.memorize
def app_browse_use_case(
        browse_repository:
        interfaces.AbsBrowseRepository = Depends(get_browse_repo),
        users_repo: st_interfaces.AbsUsersRepo = Depends(get_users_repo),
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
        meta_repo: st_interfaces.AbsMetainfoRepo = Depends(get_metainfo_repo),
) -> use_cases.AppBrowseUseCase:
    """Get use case instance."""
    return use_cases.AppBrowseUseCase(
        browse_repo=browse_repository,
        users_repo=users_repo,
        items_repo=items_repo,
        meta_repo=meta_repo
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
        users_repo: st_interfaces.AbsUsersRepo = Depends(get_users_repo),
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> use_cases.AppUploadUseCase:
    """Get use case instance."""
    return use_cases.AppUploadUseCase(
        items_repo=items_repo,
        users_repo=users_repo,
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
        users_repo: st_interfaces.AbsUsersRepo = Depends(get_users_repo),
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> use_cases.AppItemCreateUseCase:
    """Get use case instance."""
    return use_cases.AppItemCreateUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
    )


@utils.memorize
def app_item_update_use_case(
        users_repo: st_interfaces.AbsUsersRepo = Depends(get_users_repo),
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
        meta_repo: st_interfaces.AbsMetainfoRepo = Depends(get_metainfo_repo),
) -> use_cases.AppItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.AppItemUpdateUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
    )


@utils.memorize
def app_item_delete_use_case(
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> use_cases.AppItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.AppItemDeleteUseCase(
        items_repo=items_repo,
    )


@utils.memorize
def api_items_download_use_case(
    items_repo: Annotated[interfaces.AbsItemsRepo, Depends(get_items_repo)],
    meta_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[st_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
) -> use_cases.ApiItemsDownloadUseCase:
    """Get use case instance."""
    return use_cases.ApiItemsDownloadUseCase(
        items_repo=items_repo,
        metainfo_repo=meta_repo,
        misc_repo=misc_repo,
    )


# api item related use cases --------------------------------------------------


@utils.memorize
def api_item_create_use_case(
    users_repo: Annotated[st_interfaces.AbsUsersRepo, Depends(get_users_repo)],
    items_repo: Annotated[interfaces.AbsItemsRepo, Depends(get_items_repo)],
    meta_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[st_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
) -> use_cases.ApiItemCreateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemCreateUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
        misc_repo=misc_repo,
    )


@utils.memorize
def api_item_create_bulk_use_case(
    users_repo: Annotated[st_interfaces.AbsUsersRepo, Depends(get_users_repo)],
    items_repo: Annotated[interfaces.AbsItemsRepo, Depends(get_items_repo)],
    meta_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[st_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
) -> use_cases.ApiItemCreateBulkUseCase:
    """Get use case instance."""
    return use_cases.ApiItemCreateBulkUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
        misc_repo=misc_repo,
    )


@utils.memorize
def api_item_read_use_case(
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> use_cases.ApiItemReadUseCase:
    """Get use case instance."""
    return use_cases.ApiItemReadUseCase(
        items_repo=items_repo,
    )


@utils.memorize
def api_item_read_by_name_use_case(
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> use_cases.ApiItemReadByNameUseCase:
    """Get use case instance."""
    return use_cases.ApiItemReadByNameUseCase(
        items_repo=items_repo,
    )


@utils.memorize
def api_item_update_use_case(
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
        meta_repo: st_interfaces.AbsMetainfoRepo = Depends(get_metainfo_repo),
) -> use_cases.ApiItemUpdateUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateUseCase(
        items_repo=items_repo,
        metainfo_repo=meta_repo,
    )


@utils.memorize
def api_item_update_tags_use_case(
    users_repo: Annotated[st_interfaces.AbsUsersRepo, Depends(get_users_repo)],
    items_repo: Annotated[interfaces.AbsItemsRepo, Depends(get_items_repo)],
    meta_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[st_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
) -> use_cases.ApiItemUpdateTagsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateTagsUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
        misc_repo=misc_repo,
    )


@utils.memorize
def api_item_update_permissions_use_case(
    users_repo: Annotated[st_interfaces.AbsUsersRepo, Depends(get_users_repo)],
    items_repo: Annotated[interfaces.AbsItemsRepo, Depends(get_items_repo)],
    meta_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[st_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
) -> use_cases.ApiItemUpdatePermissionsUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdatePermissionsUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
        misc_repo=misc_repo,
    )


@utils.memorize
def api_item_copy_image_use_case(
        policy: Annotated[AbsPolicy, Depends(get_policy)],
        items_repo: Annotated[interfaces.AbsItemsRepo,
                              Depends(get_items_repo)],
        metainfo_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                                 Depends(get_metainfo_repo)],
        media_repository: Annotated[AbsMediaRepository, Depends(media_repo)],
) -> use_cases.ApiCopyImageUseCase:
    """Get use case instance."""
    return use_cases.ApiCopyImageUseCase(
        policy=policy,
        items_repo=items_repo,
        metainfo_repo=metainfo_repo,
        media_repo=media_repository,
    )


@utils.memorize
def api_item_update_parent_use_case(
    policy: Annotated[AbsPolicy, Depends(get_policy)],
    users_repo: Annotated[st_interfaces.AbsUsersRepo,
                          Depends(get_users_repo)],
    items_repo: Annotated[interfaces.AbsItemsRepo,
                          Depends(get_items_repo)],
    metainfo_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                             Depends(get_metainfo_repo)],
    media_repository: Annotated[AbsMediaRepository,
                                Depends(media_repo)],
    misc_repo: Annotated[st_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
) -> use_cases.ApiItemUpdateParentUseCase:
    """Get use case instance."""
    return use_cases.ApiItemUpdateParentUseCase(
        policy=policy,
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=metainfo_repo,
        media_repo=media_repository,
        misc_repo=misc_repo,
    )


@utils.memorize
def api_item_delete_use_case(
    users_repo: Annotated[st_interfaces.AbsUsersRepo, Depends(get_users_repo)],
    items_repo: Annotated[interfaces.AbsItemsRepo, Depends(get_items_repo)],
    meta_repo: Annotated[st_interfaces.AbsMetainfoRepo,
                         Depends(get_metainfo_repo)],
    misc_repo: Annotated[st_interfaces.AbsMiscRepo, Depends(get_misc_repo)],
) -> use_cases.ApiItemDeleteUseCase:
    """Get use case instance."""
    return use_cases.ApiItemDeleteUseCase(
        users_repo=users_repo,
        items_repo=items_repo,
        metainfo_repo=meta_repo,
        misc_repo=misc_repo,
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


# app profile related use cases -----------------------------------------------


@utils.memorize
def profile_quotas_use_case(
        mediator: Mediator = Depends(get_mediator),
        users_repo: st_interfaces.AbsUsersRepo = Depends(get_users_repo),
        items_repo: interfaces.AbsItemsRepo = Depends(get_items_repo),
) -> use_cases.AppProfileQuotasUseCase:
    """Get use case instance."""
    return use_cases.AppProfileQuotasUseCase(
        mediator=mediator,
        users_repo=users_repo,
        items_repo=items_repo,
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
