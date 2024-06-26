from unittest import mock
from .. import magic_calender as mc
from datetime import date


def test_magic_day_init(example_config, example_img, example_grid, example_json):
    appointments = {mc.appointment(app) for app in example_json}
    example_grid.draw(example_img)
    day = mc.magic_day(6, appointments, example_config)
    assert len(day._appointments) == 2
    assert day._appointments[0] in appointments


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
        mock_appointment_draw.return_value = 20
        appointments = {mc.appointment(app) for app in example_json}
        example_grid.draw(example_img)
        day = mc.magic_day(6, appointments, example_config)
        day.draw(config=example_config, grid=example_grid, img=example_img)
        print("\n")
        for app in day._appointments:
            print(app)
        assert mock_appointment_draw.call_count == 2
        for i, call in enumerate(mock_appointment_draw.call_args_list):
            assert int(call.args[3]) == (
                61
                + example_config.line_spacing_px
                + i * mock_appointment_draw.return_value
            )
