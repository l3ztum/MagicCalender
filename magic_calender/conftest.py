import pytest
from PIL import Image, ImageFont, ImageDraw
import json
import os
from pathlib import Path

from magic_calender.config import CalConfig
from core.grid import Grid

@pytest.fixture
def example_config() -> CalConfig:
    return CalConfig(
        month=12,
        year=2023,
        line_ink=(0, 0, 0, 0),
        appointment_spacing_px=10,
        day_spacing_px=5,
        line_width=2,
        header_spacing_px=100,
        height=1100,
        width=1000,
        render_grid=True,
        font=ImageFont.truetype(
            "arial.ttf"
            if "nt" in os.name.lower()
            else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            11 if "nt" in os.name.lower() else 12,
        ),
    )

def pytest_configure():
    pytest.test_counter = 0

@pytest.fixture
def example_img(example_config) -> ImageDraw:
    with Image.new(
        "RGBA",
        (example_config.width, example_config.height),
        color=(255, 255, 255, 255),
    ) as img:
        yield ImageDraw.Draw(img)
        print(f"\n{Path().absolute()/f'test_{pytest.test_counter}.png'}")
        img.save(Path().absolute() / f"test_{pytest.test_counter}.png")
        pytest.test_counter+=1


@pytest.fixture
def example_grid(example_config) -> Grid:
    return Grid(example_config)


@pytest.fixture
def example_json():
    with (Path(__file__).parent.absolute() / "example.json").open("r") as example_file:
        return json.load(example_file)
