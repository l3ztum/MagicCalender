from .. import magic_calender as mc


def test_magic_calender_load(example_config):
    mcal = mc.magic_calender(example_config)
    # with pytest.raises():
    mcal.load()


def test_magic_calender_load_from_json(example_config, example_json):
    mcal = mc.magic_calender(example_config)
    print(type(example_json))
    mcal.load(example_json)
