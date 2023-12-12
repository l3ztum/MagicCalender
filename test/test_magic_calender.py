from .. import magic_calender as mc
import json
import pytest
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import numpy as np


@pytest.fixture
def example_numpy():
    return np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])


@pytest.fixture
def example_json():
    with Path("./test/example.json").open("r") as example_file:
        return json.load(example_file)


@pytest.fixture
def example_config():
    return mc.CalConfig(
        month=12,
        year=2023,
        line_ink=(0, 0, 0, 0),
        line_spacing_px=10,
        line_width=2,
        header_spacing_px=100,
        height=1100,
        width=1000,
        font=ImageFont.truetype("arial.ttf", 15),
    )


@pytest.fixture
def example_imgdraw(example_config):
    with Image.new(
        "RGBA",
        (example_config.width, example_config.height),
        color=(255, 255, 255, 255),
    ) as img:
        yield ImageDraw.Draw(img)
        print(Path.cwd() / "test.png")
        img.save(Path.cwd() / "test.png")


def test_magic_appointment_load(example_json):
    ap = mc.appointment(example_json)
    ap.load()
    assert ap.start == datetime.fromisoformat("2023-12-05")
    assert ap.end == datetime.fromisoformat("2023-12-06T06:09:23")
    assert ap.summary == "Example event"


def test_magic_appointment_load_fails():
    example_json = json.loads(
        '{"start": {"date": "2023-12-05"}, "end":{"dateTime": "2023-12-06T06:09:23Z" }, "summary": "Example event"}'
    )
    ap = mc.appointment(example_json)
    ap.load()
    assert ap.start == datetime.fromisoformat("2023-12-05")
    assert ap.end == datetime.fromisoformat("2023-12-06T06:09:23")
    assert ap.summary == "Example event"


def test_magic_appointment_text_cut(example_json, example_config):
    ap = mc.appointment(example_json)
    ap.load()
    example_config.width = 110
    example_config.line_spacing_px = 10
    ap.summary = "This text should be longer than 100px"
    length = example_config.font.getlength(ap.summary)
    assert length > 100
    short = ap._get_summary(100, example_config)
    assert short == ap.summary[:13] + "\u2026"


def test_magic_appointment_draw(example_json, example_imgdraw, example_config):
    ap = mc.appointment(example_json)
    ap.load()
    ap.summary = "Long Example Event Summary"
    grid = mc.Grid(example_config)
    grid.draw(example_imgdraw)
    ap.draw(0, example_imgdraw, grid, example_config)


def test_box_draw(example_config, example_imgdraw):
    box = mc.Box(mc.Point(10, 100), mc.Point(100, 200))
    box.draw(example_config, example_imgdraw)


def test_grid_coords(example_config, example_imgdraw):
    print(example_config)
    grid = mc.Grid(example_config)
    grid._cal = np.array(
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
    )
    assert (
        mc.Box(
            mc.Point(0, example_config.header_spacing_px),
            mc.Point(250, example_config.header_spacing_px + 250),
        ).as_tuple()
        == grid._coords_from_index(0, 0).as_tuple()
    )
    assert (0, 350, 250, 600) == grid.get_coords_to_draw(5).as_tuple()
    grid.draw(example_imgdraw)
