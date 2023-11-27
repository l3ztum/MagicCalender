import pytest
from .. import magic_calender as mc


def test_equality():
    assert mc.Point(1, 1) == mc.Point(1, 1)
    assert mc.Point(1, 1) < mc.Point(2, 2)
    assert mc.Point(1, 1) < mc.Point(1, 2)


def test_add():
    assert mc.Point(1, 1) + 1 == mc.Point(2, 2)
    assert mc.Point(1, 1) + (1, 2) == mc.Point(2, 3)
    assert mc.Point(1, 1) + mc.Point(2, 2) == mc.Point(3, 3)


def test_cast():
    y, x = mc.Point(4, 4).as_tuple()
    assert y == x == 4
