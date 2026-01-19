import pytest

from MagicCalender.lib.point import Point
from MagicCalender.lib.box import Box


def test_box_init():
    assert (
        Box(Point(1, 1), Point(2, 2))
        == Box.fromtuple((1, 1, 2, 2))
    )


def test_in_box():
    box = Box.fromtuple((10, 10, 20, 20))
    assert box.is_in_box(Point(15, 15))
    assert box.is_in_box(Point(19, 20))
    assert box.is_in_box(Point(10, 11))
    assert not box.is_in_box(Point(0, 0))
    assert not box.is_in_box(Point(21, 21))


def test_box_draw(example_config, example_img):
    box = Box.fromtuple((100, 100, 200, 200))
    box.draw(example_config, example_img)


def test_box_encapsulating_square():
    box = Box.fromtuple((100, 100, 300, 200))
    assert box.midpoint() == Point(200, 150)
    square = box.encapsulating_square()
    assert Box.fromtuple((100, 50, 300, 250)) == square

def test_box_resize():
    box = Box.fromtuple((100, 100, 200, 200))
    box.resize(5)
    assert box == Box.fromtuple((95, 95, 205, 205)), print(f"{box}")
    box.resize((5, 5, -5, -5))
    assert box == Box.fromtuple((100, 100, 200, 200)), print(f"{box}")