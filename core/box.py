from typing import Tuple, overload

from PIL.ImageDraw import ImageDraw

from core.point import Point
from magic_calender.config import CalConfig

class Box:
    def __init__(self, p_start: Point, p_end: Point) -> None:
        assert p_start < p_end
        self.p_start: Point = p_start
        self.p_end: Point = p_end
        self._p2: Point
        self._p3: Point
        self._fill_other()

    def _fill_other(self):
        self._p2 = Point(self.p_end.x, self.p_start.y)
        self._p3 = Point(self.p_start.x, self.p_end.y)

    def __add__(self, to_add):
        "Adds given pixel outwards in each direction"
        self.p_start -= to_add
        self.p_end += to_add
        self._fill_other()
        return self

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Box):
            return self.p_start == other.p_start and self.p_end == other.p_end
        return False

    @classmethod
    def fromtuple(cls, points: Tuple[int, int, int, int]):
        assert len(points) == 4
        return cls(Point(points[0], points[1]), Point(points[2], points[3]))

    @property
    def width(self):
        return abs(self.p_end.x - self.p_start.x)

    @property
    def height(self):
        return abs(self.p_end.y - self.p_start.y)

    def midpoint(self) -> Point:
        p = self.p_end - self.p_start
        return self.p_end - Point(*[i / 2 for i in p.as_tuple()])

    @overload
    def resize(self, other: int) -> None:
        ...

    @overload
    def resize(self, other: Tuple[int, int, int, int]) -> None:
        ...

    def resize(self, other):
        if isinstance(other, int):
            self.p_start -= other
            self.p_end += other
        elif isinstance(other, tuple):
            assert len(other) == 4
            self.p_start += other[:2]
            self.p_end += other[2:]
        else:
            raise NotImplementedError

    def encapsulating_square(self):
        p = self.p_end - self.p_start
        side_length_2 = int(max(p.as_tuple()) / 2)
        midpoint = self.midpoint()
        return Box(midpoint - side_length_2, midpoint + side_length_2)

    def anker_to(self, point: Point):
        self.p_start += point
        self.p_end += point
        self._fill_other()

    def __sub__(self, other):
        if isinstance(other, Box):
            return Box(self.p_start - other.p_start, self.p_end - other.p_end)
        raise TypeError

    def is_in_box(self, p: Point) -> bool:
        return p > self.p_start and p < self.p_end

    def __str__(self) -> str:
        return f"Box from {self.p_start} to {self.p_end}"

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.p_start.as_tuple() + self.p_end.as_tuple()

    def get_rel_box(self, absolute):
        if isinstance((absolute), Box):
            return self - absolute

    def get_abs_box(self, relative):
        if isinstance((relative), Box):
            return self + relative

    def draw(self, CalConfig: CalConfig, img: ImageDraw):
        to_draw = (
            self.p_start.as_tuple() + self._p2.as_tuple(),
            self._p2.as_tuple() + self.p_end.as_tuple(),
            self._p3.as_tuple() + self.p_end.as_tuple(),
            self.p_start.as_tuple() + self._p3.as_tuple(),
        )
        for points in to_draw:
            img.line(
                points,
                fill=CalConfig.line_ink,
                width=CalConfig.line_width,
            )
