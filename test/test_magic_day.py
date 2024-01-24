from unittest import mock
from .. import magic_calender as mc
from datetime import date


def test_magic_day_init(example_config, example_img, example_grid, example_json):
    appointments = {mc.appointment(app) for app in example_json}
    example_grid.draw(example_img)
    day = mc.magic_day(6, appointments, example_config)
    assert len(day._appointments) == 2


def test_magic_day_draw(example_config, example_img, example_grid, example_json):
    with mock.patch(f"{mc.__name__}.date", wraps=date) as mock_date:
        mock_date.today.return_value = date(2023, 12, 6)
        appointments = [mc.appointment(app) for app in example_json]
        example_grid.draw(example_img)
        day = mc.magic_day(6, appointments, example_config)
        day.draw(example_config, example_grid, example_img)
        print("\n")
        for app in day._appointments:
            print(app)


def test_magic_day_draw_calls(example_config, example_img, example_grid, example_json):
    with mock.patch(f"{mc.__name__}.date", wraps=date) as mock_date, mock.patch(
        f"{mc.__name__}.appointment.draw"
    ) as mock_appointment_draw:
        mock_date.today.return_value = date(2023, 12, 6)
        appointments = {mc.appointment(app) for app in example_json}
        example_grid.draw(example_img)
        day = mc.magic_day(6, appointments, example_config)
        day.draw(config=example_config, grid=example_grid, img=example_img)
        print("\n")
        for app in day._appointments:
            print(app)
        print(mock_appointment_draw.call_args_list)
        assert mock_appointment_draw.call_count == 2
