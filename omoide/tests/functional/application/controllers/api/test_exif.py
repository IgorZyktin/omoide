"""Tests.
"""
import pytest
import pytest_asyncio

from omoide.domain import errors
from omoide.domain.core import core_models
from omoide.storage.repositories.asyncpg.rp_exif import EXIFRepository
from omoide.tests import utils
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

    await exif_repo.delete_exif(item.uuid)
    yield
    await exif_repo.delete_exif(item.uuid)


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

    read_uc = uc_api_exif.ReadEXIFUseCase(exif_repo)
    create_uc = uc_api_exif.CreateEXIFUseCase(exif_repo)
    update_uc = uc_api_exif.UpdateEXIFUseCase(exif_repo)
    delete_uc = uc_api_exif.DeleteEXIFUseCase(exif_repo)

    exif_before = core_models.EXIF(
        item_uuid=item.uuid,
        exif={'foo': {'bar': 'baz'}},
    )

    exif_after = core_models.EXIF(
        item_uuid=item.uuid,
        exif={'something': [1, 2, 3]},
    )

    # ensure emptiness --------------------------------------------------------
    response_1 = await read_uc.execute(policy, user, item.uuid)
    utils.assert_error(response_1, errors.EXIFDoesNotExist)

    # create ------------------------------------------------------------------
    response_2 = await create_uc.execute(policy, user, item.uuid, exif_before)
    assert not isinstance(response_2, errors.Error)
    assert response_2 == exif_before

    # read --------------------------------------------------------------------
    response_3 = await read_uc.execute(policy, user, item.uuid)
    assert not isinstance(response_3, errors.Error)
    assert response_3 == exif_before

    # update ------------------------------------------------------------------
    response_4 = await update_uc.execute(policy, user, item.uuid, exif_after)
    assert not isinstance(response_4, errors.Error)
    assert response_4 != exif_before
    assert response_4 == exif_after

    # read --------------------------------------------------------------------
    response_5 = await read_uc.execute(policy, user, item.uuid)
    assert not isinstance(response_5, errors.Error)
    assert response_5 != exif_before
    assert response_5 == exif_after

    # delete ------------------------------------------------------------------
    response_6 = await delete_uc.execute(policy, user, item.uuid)
    assert not isinstance(response_6, errors.Error)
    assert response_6 is None

    # read --------------------------------------------------------------------
    response_7 = await read_uc.execute(policy, user, item.uuid)
    utils.assert_error(response_7, errors.EXIFDoesNotExist)


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

    create_uc = uc_api_exif.CreateEXIFUseCase(exif_repo)

    exif = core_models.EXIF(
        item_uuid=item.uuid,
        exif={'foo': {'bar': 'baz'}},
    )

    # create ------------------------------------------------------------------
    response_1 = await create_uc.execute(policy, user, item.uuid, exif)
    assert not isinstance(response_1, errors.Error)
    assert response_1 == exif

    # create again ------------------------------------------------------------
    response_2 = await create_uc.execute(policy, user, item.uuid, exif)
    utils.assert_error(response_2, errors.EXIFAlreadyExist)


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

    update_uc = uc_api_exif.UpdateEXIFUseCase(exif_repo)

    exif = core_models.EXIF(
        item_uuid=item.uuid,
        exif={'foo': {'bar': 'baz'}},
    )

    # act
    response = await update_uc.execute(policy, user, item.uuid, exif)

    # assert
    utils.assert_error(response, errors.EXIFDoesNotExist)
