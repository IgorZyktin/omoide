"""Tests.
"""
import pytest
import pytest_asyncio

from omoide.domain import errors
from omoide.domain.core import core_models
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Success
from omoide.storage.repositories.asyncpg.rp_exif import EXIFRepository
from omoide.use_cases.api import uc_api_exif


@pytest.fixture(scope='session')
def functional_tests_exif_repo(functional_tests_database):
    return EXIFRepository(functional_tests_database)


@pytest_asyncio.fixture(scope='session')
async def ensure_there_is_no_exif(
        functional_tests_permanent_item,
        functional_tests_exif_repo,
):
    # clear before
    await functional_tests_exif_repo.delete_exif(
        functional_tests_permanent_item.uuid,
    )
    yield
    # clear after
    await functional_tests_exif_repo.delete_exif(
        functional_tests_permanent_item.uuid,
    )


@pytest.mark.usefixtures('ensure_there_is_no_exif')
async def test_exif_crud(
        functional_tests_permanent_user,
        functional_tests_permanent_item,
        functional_tests_policy,
        functional_tests_exif_repo,
):
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
    assert isinstance(response_1, Failure)
    assert isinstance(response_1.error, errors.EXIFDoesNotExist)

    # create ------------------------------------------------------------------
    response_2 = await create_uc.execute(policy, user, item.uuid, exif_before)
    assert isinstance(response_2, Success)
    assert response_2.value == exif_before

    # read --------------------------------------------------------------------
    response_3 = await read_uc.execute(policy, user, item.uuid)
    assert isinstance(response_3, Success)
    assert response_3.value == exif_before

    # update ------------------------------------------------------------------
    response_4 = await update_uc.execute(policy, user, item.uuid, exif_after)
    assert isinstance(response_4, Success)
    assert response_4.value != exif_before
    assert response_4.value == exif_after

    # read --------------------------------------------------------------------
    response_5 = await read_uc.execute(policy, user, item.uuid)
    assert isinstance(response_5, Success)
    assert response_5.value != exif_before
    assert response_5.value == exif_after

    # delete ------------------------------------------------------------------
    response_6 = await delete_uc.execute(policy, user, item.uuid)
    assert isinstance(response_6, Success)
    assert response_6.value is None

    # read --------------------------------------------------------------------
    response_1 = await read_uc.execute(policy, user, item.uuid)
    assert isinstance(response_1, Failure)
    assert isinstance(response_1.error, errors.EXIFDoesNotExist)
