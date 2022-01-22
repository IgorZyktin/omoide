# -*- coding: utf-8 -*-
"""Tests.
"""
import time

from omoide.presentation import infra


def test_timer():
    with infra.Timer() as timer:
        time.sleep(0.001)
    assert timer.seconds >= 0.001
