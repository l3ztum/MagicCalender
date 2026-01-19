from __future__ import annotations

from typing import Tuple

class Point:
    
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y

    def __gt__(self, other):
        return self.x > other.x or self.y > other.y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __str__(self) -> str:
        return f"Point({self.x},{self.y})"

    def __add__(self, other):
        if isinstance(other, int):
            return Point(self.x + other, self.y + other)
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        elif isinstance(other, tuple):
            return Point(self.x + other[0], self.y + other[1])
        else:
            return self

    def __sub__(self, other):
        if isinstance(other, int):
            return self + other * (-1)
        if isinstance(other, Point):
            return self + Point(*[i * -1 for i in other.as_tuple()])

    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)