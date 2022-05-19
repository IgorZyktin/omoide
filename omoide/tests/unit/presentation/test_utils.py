# -*- coding: utf-8 -*-
"""Tests.
"""
from omoide import utils


def test_sep_digits():
    """Must separate digits on 1000s."""
    assert utils.sep_digits('12345678') == '12345678'
    assert utils.sep_digits(12345678) == '12 345 678'
    assert utils.sep_digits(1234.5678) == '1 234.57'
    assert utils.sep_digits(1234.5678, precision=4) == '1 234.5678'
    assert utils.sep_digits(1234.0, precision=4) == '1 234.0000'
    assert utils.sep_digits(1234.0, precision=0) == '1 234'
