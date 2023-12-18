import pytest
from .. import magic_calender as mc
from PIL import Image, ImageFont, ImageDraw
import json
import os
from pathlib import Path
import numpy as np


@pytest.fixture
def example_config() -> mc.CalConfig:
    return mc.CalConfig(
        month=12,
        year=2023,
        line_ink=(0, 0, 0, 0),
        line_spacing_px=10,
        day_spacing_px=5,
        line_width=2,
        header_spacing_px=100,
        height=1100,
        width=1000,
        font=ImageFont.truetype(
            "arial.ttf"
            if "nt" in os.name.lower()
            else "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
            15,
        ),
    )


@pytest.fixture
def example_numpy():
    return np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])


@pytest.fixture
def example_img(example_config) -> ImageDraw:
    with Image.new(
        "RGBA",
        (example_config.width, example_config.height),
        color=(255, 255, 255, 255),
    ) as img:
        yield ImageDraw.Draw(img)
        print(f"\n{Path().absolute()/'test.png'}")
        img.save(Path().absolute() / "test.png")


@pytest.fixture
def example_grid(example_config) -> mc.Grid:
    return mc.Grid(example_config)


@pytest.fixture
def example_json():
    with (Path(__file__).parent.absolute() / "example.json").open("r") as example_file:
        return json.load(example_file)
