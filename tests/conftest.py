import pytest
from .. import magic_calender as mc
from PIL import ImageFont


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
