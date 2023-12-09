import pytest
from .. import magic_calender as mc


def test_magic_day_draw(example_config, example_img, example_grid):
    day = mc.magic_day(6)
    day.draw(example_grid, example_config, example_img)
