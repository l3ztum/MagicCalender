from __future__ import annotations
import os
import json

from dataclasses import dataclass
from datetime import date
from typing import Any
from pathlib import Path

from PIL import ImageFont

@dataclass
class CalConfig:
    month: int = date.today().month
    year: int = date.today().year
    line_ink: Any = (0, 0, 0, 0)
    appointment_spacing_px: int = 5
    appointment_padding_px: int = 8
    day_spacing_px: int = 5
    line_width: int = 2
    header_spacing_px: int = 350
    height: int = 1920
    width: int = 1080
    render_grid: bool = True
    draw_background: bool = True
    number_size:float = 60
    font: ImageFont.FreeTypeFont = ImageFont.truetype(
        "arial.ttf"
        if "nt" in os.name.lower()
        else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        12,
    )

    # @staticmethod
    # def as_CalConfig(dict):
    #     if 'CalConfig':
    @staticmethod
    def from_json(json_path:Path)->CalConfig:
        with json_path.open("r") as file:
            json.load(file)