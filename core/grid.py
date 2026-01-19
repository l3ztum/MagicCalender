
from typing import Tuple, Optional


from enum import Enum
from calendar import monthcalendar

from PIL.ImageDraw import ImageDraw


from magic_calender.core.box import Box
from magic_calender.core.point import Point
from magic_calender.config import CalConfig


class ORIENTATION(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

class Grid:
    def __init__(self, CalConfig: CalConfig) -> None:
        self._orientation = (
            ORIENTATION.HORIZONTAL
            if CalConfig.height < CalConfig.width
            else ORIENTATION.VERTICAL
        )
        self._config = CalConfig
        self._cal = monthcalendar(self._config.year, self._config.month)

    def _where(self, day: int) -> Tuple[int, int]:
        return [
            (row, col)
            for row, x in enumerate(self._cal)
            for col, i in enumerate(x)
            if i == day
        ][0]

    def is_weekend(self, day: int):
        _, col = self._where(day)
        return col >= 5

    def get_coords_to_draw(self, day: int, multiday:Optional[int]=None) -> Box:
        row, col = self._where(day)
        return self._coords_from_index(row, col, multiday)

    def _get_dimensions(self) -> Tuple[int, int]:
        return max(
            [
                (row, col)
                for row, x in enumerate(self._cal, 1)
                for col, _ in enumerate(x, 1)
            ]
        )

    def _coords_from_index(self, row, col, multiday:Optional[int]=None) -> Box:
        max_rows_to_draw, max_cols_to_draw = self._get_dimensions()
        height_per_row = int(
            (self._config.height - self._config.header_spacing_px) / max_rows_to_draw
        )
        width_per_col = int(self._config.width / max_cols_to_draw)
        p_start = Point(
            width_per_col * (col),
            int(self._config.header_spacing_px + (height_per_row * (row))),
        )
        days=1
        if multiday and col != max_cols_to_draw:
            print(f"{multiday},{max_cols_to_draw - col}")
            days=min(multiday, max_cols_to_draw - col)
        p_end = Point(
            int(p_start.x + days*width_per_col),
            int(p_start.y + height_per_row),
        )
        return Box(p_start, p_end)

    def draw(self, img: ImageDraw):
        if self._config.render_grid:
            rows, cols = self._get_dimensions()
            for row in range(rows):
                for col in range(cols):
                    self._coords_from_index(row, col).draw(self._config, img)
