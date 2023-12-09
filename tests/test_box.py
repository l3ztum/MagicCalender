import pytest

from .. import magic_calender as mc


def test_box_init():
    assert (
        mc.Box(mc.Point(1, 1), mc.Point(2, 2)).as_tuple()
        == mc.Box.fromtuple((1, 1, 2, 2)).as_tuple()
    )


def test_in_box():
    box = mc.Box.fromtuple((10, 10, 20, 20))
    assert box.is_in_box(mc.Point(15, 15))
    assert box.is_in_box(mc.Point(19, 20))
    assert box.is_in_box(mc.Point(10, 11))
    assert not box.is_in_box(mc.Point(0, 0))
    assert not box.is_in_box(mc.Point(21, 21))


def test_box_draw(example_config, example_img):
    box = mc.Box.fromtuple((100, 100, 200, 200))
    box.draw(example_config, example_img)
