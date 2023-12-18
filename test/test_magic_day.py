from unittest import mock
from .. import magic_calender as mc
from datetime import date, datetime


def test_magic_day_init(example_config, example_img, example_grid, example_json):
    appointments = [mc.appointment(app) for app in example_json]
    example_grid.draw(example_img)
    day = mc.magic_day(6, appointments, example_config)
    assert len(day._appointments) == 2
    assert day._appointments[0] == appointments[0]


def test_magic_day_draw(example_config, example_img, example_grid, example_json):
    with mock.patch(f"{mc.__name__}.date", wraps=date) as mock_date:
        mock_date.today.return_value = date(2023, 12, 6)
        appointments = [mc.appointment(app) for app in example_json]
        example_grid.draw(example_img)
        print("\n")
        for app in appointments:
            print(app)
        day = mc.magic_day(6, appointments, example_config)
        day.draw(example_grid, example_config, example_img)
