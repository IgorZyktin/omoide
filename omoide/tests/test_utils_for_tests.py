"""Tests for test infrastructure.
"""
import pytest

from omoide.domain import errors
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Success
from omoide.tests import utils


class Error1(errors.Error):
    """Dummy error for tests."""


class Error2(errors.Error):
    """Dummy error for tests."""


class Error3(errors.Error):
    """Dummy error for tests."""


def test_resolve_error_bad_input_type():
    """Must raise on incorrect type."""
    # arrange
    result = Success(value='bad')

    # assert
    msg = 'Expected to get Failure, got Success instead'
    with pytest.raises(TypeError, match=msg):
        utils.resolve_error(result, errors.Error)


def test_resolve_error_bad_error_type():
    """Must raise on incorrect type."""
    # arrange
    result = Failure(error=Error1())

    # assert
    msg = 'Expected to get type Error2, got type Error1'
    with pytest.raises(TypeError, match=msg):
        utils.resolve_error(result, Error2)


def test_resolve_error_bad_error_types():
    """Must raise on incorrect type."""
    # arrange
    result = Failure(error=Error1())

    # assert
    msg = (r"Expected to get one of types \('Error2', 'Error3'\), "
           r"got type Error1")
    with pytest.raises(TypeError, match=msg):
        utils.resolve_error(
            result,
            (Error2, Error3),
        )


def test_resolve_error_good_regex():
    """Must point out that regex could be incorrectly read."""
    # arrange
    result = Failure(error=errors.Error(template='test'))

    # assert
    assert utils.resolve_error(result, errors.Error, 'test') == result.error


def test_resolve_error_bad_not_found_regex():
    """Must fail because of unmatched regex."""
    # arrange
    result = Failure(error=errors.Error(template='foo'))

    # assert
    msg = 'Regex pattern did not match'
    with pytest.raises(ValueError, match=msg):
        utils.resolve_error(result, errors.Error, 'test')


def test_resolve_success_good():
    """Must return result."""
    # arrange
    result = Success(value='good')

    # assert
    assert utils.resolve_success(result) == result.value


def test_resolve_success_bad_input_type():
    """Must raise on incorrect type."""
    # arrange
    result = Failure(error=errors.Error())

    # assert
    msg = 'Expected to get Success, got Failure instead'
    with pytest.raises(TypeError, match=msg):
        utils.resolve_success(result)
