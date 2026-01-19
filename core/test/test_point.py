import pytest

from MagicCalender.lib.point import Point

def test_equality():
    assert Point(1, 1) == Point(1, 1)
    assert Point(1, 1) < Point(2, 2)
    assert Point(1, 1) < Point(1, 2)


def test_add():
    assert Point(1, 1) + 1 == Point(2, 2)
    assert Point(1, 1) + (1, 2) == Point(2, 3)
    assert Point(1, 1) + Point(2, 2) == Point(3, 3)


def test_cast():
    y, x = Point(4, 4).as_tuple()
    assert y == x == 4
