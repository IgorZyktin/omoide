"""Tests.
"""
import pytest
import pytest_asyncio

from omoide.domain import exceptions
from omoide.domain.core import core_models
from omoide.storage.repositories.asyncpg.rp_exif import EXIFRepository
from omoide.use_cases.api import uc_api_exif


@pytest.fixture(scope='session')
def functional_tests_exif_repo(functional_tests_database):
    """Return repository for functional tests."""
    return EXIFRepository(functional_tests_database)


@pytest_asyncio.fixture
async def ensure_there_is_no_exif(
        functional_tests_permanent_item,
        functional_tests_exif_repo,
):
    """Delete all corresponding EXIFs before and after all tests."""
    item = functional_tests_permanent_item
    exif_repo = functional_tests_exif_repo

    try:
        await exif_repo.delete_exif(item.uuid)
    except exceptions.EXIFDoesNotExistError:
        pass

    yield

    try:
        await exif_repo.delete_exif(item.uuid)
    except exceptions.EXIFDoesNotExistError:
        pass


@pytest.mark.usefixtures('ensure_there_is_no_exif')
async def test_exif_crud(
        functional_tests_permanent_user,
        functional_tests_permanent_item,
        functional_tests_policy,
        functional_tests_exif_repo,
):
    """Test whole EXIF life cycle."""
    # arrange
    user = functional_tests_permanent_user
    item = functional_tests_permanent_item
    policy = functional_tests_policy
    exif_repo = functional_tests_exif_repo

    read_uc = uc_api_exif.ReadEXIFUseCase(policy, exif_repo)
    create_uc = uc_api_exif.CreateEXIFUseCase(policy, exif_repo)
    update_uc = uc_api_exif.UpdateEXIFUseCase(policy, exif_repo)
    delete_uc = uc_api_exif.DeleteEXIFUseCase(policy, exif_repo)

    exif_before = core_models.EXIF(
        item_uuid=item.uuid,
        exif={'foo': {'bar': 'baz'}},
    )

    exif_after = core_models.EXIF(
        item_uuid=item.uuid,
        exif={'something': [1, 2, 3]},
    )

    # ensure emptiness --------------------------------------------------------
    with pytest.raises(exceptions.EXIFDoesNotExistError):
        await read_uc.execute(user, item.uuid)

    # create ------------------------------------------------------------------
    response_2 = await create_uc.execute(user, item.uuid, exif_before)
    assert response_2 == exif_before

    # read --------------------------------------------------------------------
    response_3 = await read_uc.execute(user, item.uuid)
    assert response_3 == exif_before

    # update ------------------------------------------------------------------
    response_4 = await update_uc.execute(user, item.uuid, exif_after)
    assert response_4 != exif_before
    assert response_4 == exif_after

    # read --------------------------------------------------------------------
    response_5 = await read_uc.execute(user, item.uuid)
    assert response_5 != exif_before
    assert response_5 == exif_after

    # delete ------------------------------------------------------------------
    response_6 = await delete_uc.execute(user, item.uuid)
    assert response_6 is None

    # read --------------------------------------------------------------------
    with pytest.raises(exceptions.EXIFDoesNotExistError):
        await read_uc.execute(user, item.uuid)


@pytest.mark.usefixtures('ensure_there_is_no_exif')
async def test_exif_double_add(
        functional_tests_permanent_user,
        functional_tests_permanent_item,
        functional_tests_policy,
        functional_tests_exif_repo,
):
    """Ensure that we cannot add one exif twice."""
    # arrange
    user = functional_tests_permanent_user
    item = functional_tests_permanent_item
    policy = functional_tests_policy
    exif_repo = functional_tests_exif_repo

    create_uc = uc_api_exif.CreateEXIFUseCase(policy, exif_repo)

    exif = core_models.EXIF(
        item_uuid=item.uuid,
        exif={'foo': {'bar': 'baz'}},
    )

    # create ------------------------------------------------------------------
    response_1 = await create_uc.execute(user, item.uuid, exif)
    assert response_1 == exif

    # create again ------------------------------------------------------------
    with pytest.raises(exceptions.AlreadyExistError):
        await create_uc.execute(user, item.uuid, exif)


@pytest.mark.usefixtures('ensure_there_is_no_exif')
async def test_exif_update_nonexisting(
        functional_tests_permanent_user,
        functional_tests_permanent_item,
        functional_tests_policy,
        functional_tests_exif_repo,
):
    """Ensure that we cannot update nonexistent EXIF."""
    # arrange
    user = functional_tests_permanent_user
    item = functional_tests_permanent_item
    policy = functional_tests_policy
    exif_repo = functional_tests_exif_repo

    update_uc = uc_api_exif.UpdateEXIFUseCase(policy, exif_repo)

    exif = core_models.EXIF(
        item_uuid=item.uuid,
        exif={'foo': {'bar': 'baz'}},
    )

    # act
    with pytest.raises(exceptions.DoesNotExistError):
        await update_uc.execute(user, item.uuid, exif)
