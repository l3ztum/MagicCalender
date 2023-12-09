import pytest
from .. import magic_calender as mc
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
import json


@pytest.fixture
def example_config() -> mc.CalConfig:
    return mc.CalConfig(
        month=12,
        year=2023,
        line_ink=(0, 0, 0, 0),
        line_spacing_px=10,
        line_width=2,
        header_spacing_px=100,
        height=1100,
        width=1000,
        font=ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 11),
    )


@pytest.fixture
def example_img(example_config) -> ImageDraw:
    with Image.new(
        "RGBA",
        (example_config.width, example_config.height),
        color=(255, 255, 255, 255),
    ) as img:
        yield ImageDraw.Draw(img)
        img.save("test.png")


@pytest.fixture
def example_grid(example_config) -> mc.Grid:
    return mc.Grid(example_config)


@pytest.fixture
def example_gcal():
    return json.loads()
