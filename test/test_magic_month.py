from .. import magic_calender as mc


def test_magic_month_init(example_config, example_grid, example_json):
    appointments = [mc.appointment(app) for app in example_json]
    mm = mc.magic_month(example_config, example_grid, appointments)
    assert len(mm.days) == 31


def test_magic_month_draw(example_config, example_img, example_grid, example_json):
    appointments = [mc.appointment(app) for app in example_json]
    mm = mc.magic_month(example_config, example_grid, appointments)
    mm.draw(example_config, example_grid, example_img)
    assert len(mm.days) == 31


def test_magic_month_head_text(example_config, example_grid, example_json):
    appointments = [mc.appointment(app) for app in example_json]
    mm = mc.magic_month(example_config, example_grid, appointments)
    assert 108 == mm._get_header_text_size(example_config)
    assert len(mm.days) == 31
