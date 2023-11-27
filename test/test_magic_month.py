from .. import magic_calender as mc


def test_magic_month_init(example_config, example_grid, example_json):
    appointments = [mc.appointment(app) for app in example_json]
    mm = mc.magic_month(example_config, example_grid, appointments)
    assert len(mm.days) == 31
