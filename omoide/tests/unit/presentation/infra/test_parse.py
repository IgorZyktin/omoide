# -*- coding: utf-8 -*-
"""Parsing tests.
"""
from uuid import UUID

import pytest

from omoide.domain import exceptions
from omoide.presentation.infra import parse


def test_cast_uuid_good():
    # arrange
    data = 'de1cb027-a33b-498d-9230-446e85ee1638'

    # act
    result = parse.cast_uuid(data)

    # assert
    assert isinstance(result, UUID)


def test_cast_uuid_bad():
    # arrange
    data = 'wtf?'
    ref = 'badly formed hexadecimal UUID string'

    # act
    with pytest.raises(exceptions.IncorrectUUID, match=ref):
        parse.cast_uuid(data)
