import pytest
from .. import magic_calender as mc
import numpy as np
from calendar import monthcalendar


def test_point_operations():
    p = mc.Point(10, 6)
    p2 = mc.Point(*(np.array(p.as_tuple()) / 2))
    p3 = mc.Point(*[i / 2 for i in p.as_tuple()])
    assert p2 == p3
    assert p3 == mc.Point(5, 3)


def test_month_calender(example_config, example_grid):
    cal_np = np.array(monthcalendar(example_config.year, example_config.month))
    day = 6
    print(cal_np)
    print(example_grid._cal)
    assert example_grid._where(day) == tuple(i[0] for i in np.where(cal_np == day))
    assert example_grid._get_dimensions() == np.shape(cal_np)
