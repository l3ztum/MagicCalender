from .. import magic_calender as mc
import pytest
from pathlib import Path


def test_magic_calender_load(example_config):
    mcal = mc.magic_calender(example_config)
    with pytest.raises(RuntimeError):
        mcal.load()


def test_magic_calender_load_from_json(example_config, example_json):
    mcal = mc.magic_calender(example_config)
    print(type(example_json))
    mcal.load(example_json)


def test_magic_calender_save_to_file(example_config, example_json, tmp_path):
    mcal = mc.magic_calender(example_config)
    print(type(example_json))
    mcal.load(example_json)
    mcal.draw()
    mcal.save(tmp_path / (file := "calender.png"))
    print(tmp_path / file)
