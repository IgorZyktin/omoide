# -*- coding: utf-8 -*-
"""Tests.
"""
import http
from uuid import UUID

import pytest

from omoide import utils
from omoide.domain import errors
from omoide.presentation import web

_UUID = UUID('fb6a8840-d6a8-4ab4-9555-be67917c8717')


@pytest.mark.parametrize('error,code', [
    (errors.UserDoesNotExist(uuid=_UUID), http.HTTPStatus.NOT_FOUND),
    (errors.ItemRequiresAccess(uuid=_UUID), http.HTTPStatus.FORBIDDEN),
])
def test_get_corresponding_error_code(error, code):
    """Must return correct HTTP codes for given errors."""
    assert web.get_corresponding_error_code(error) == code


@pytest.mark.parametrize('template, kwargs, ref', [
    ('x={x}, y={y}', dict(x=1, z=2), 'x=1, y={y}'),
    ('x={x}, y={y}', dict(x=1, y=0), 'x=1, y=0'),
    ('x={x}, y={y}, m={m}', dict(x=1, y=0, f=5), 'x=1, y=0, m={m}'),
])
def test_safe_template(template, kwargs, ref):
    """Must render template without errors."""
    assert web.safe_template(template, **kwargs) == ref


def test_sep_digits():
    """Must separate digits on 1000s."""
    assert utils.sep_digits('12345678') == '12345678'
    assert utils.sep_digits(12345678) == '12 345 678'
    assert utils.sep_digits(1234.5678) == '1 234.57'
    assert utils.sep_digits(1234.5678, precision=4) == '1 234.5678'
    assert utils.sep_digits(1234.0, precision=4) == '1 234.0000'
    assert utils.sep_digits(1234.0, precision=0) == '1 234'
