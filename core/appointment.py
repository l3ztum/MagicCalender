from datetime import datetime, time, timedelta
from copy import deepcopy
from typing import Optional

import pytz
from PIL.ImageDraw import ImageDraw
from magic_calender.config import CalConfig

from core.box import Box
from core.grid import Grid

class Appointment:

    def __init__(self, gcal_event) -> None:
        self._gcal_event = gcal_event
        self.summary: str = "<error>"
        self.load()

    def __str__(self) -> str:
        return f"{self.start.isoformat()} - { self.end.isoformat() }: {self.summary}"

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Appointment):
            return False
        return self.id == __o.id

    def __lt__(self, _other: object) -> bool:
        if self.multiday == _other.multiday:
            if not self.multiday:
                return self.end.time() < _other.end.time()
            if self.end.date() == self.end.date():
                return self.end.time() < self.end.time()
            return self.end.date() < self.end.date()
        elif self.multiday != _other.multiday:
            return self.multiday

    def __hash__(self) -> id:
        return hash(self.id)

    @property
    def days(self) -> int:
        if (days:=self.end.date() - self.start.date())>timedelta(days=1):
            return days.days + 1
        else:
            return 1

    @property
    def multiday(self) -> bool:
        #return not self.start.date() == self.end.date() and timedelta(days=1)<(self.end.date()-self.start.date())
        return self.days>1

    def on_day(self,day:datetime)->bool:
        return (self.start
            <= day
            < self.end) or day.date() == self.start.date()

    def load(self):
        try:
            self.start = datetime.fromisoformat(
                self._gcal_event["start"]
                .get("dateTime", self._gcal_event["start"].get("date"))
                .rstrip("Z")
            ).replace(tzinfo=pytz.UTC)
            self.end = datetime.fromisoformat(
                str(
                    self._gcal_event["end"].get(
                        "dateTime", self._gcal_event["end"].get("date")
                    )
                ).rstrip("Z")
            ).replace(tzinfo=pytz.UTC)
            self.summary = self._gcal_event["summary"]
            self.id = self._gcal_event["id"]
        except KeyError as exc:
            raise RuntimeError(
                f"Couldn't load appointment with given data: {self._gcal_event}"
            ) from exc

    def _get_summary(self, length: int, config: CalConfig) -> str:
        summary = self.summary if self.start.time() == time(0,0) else f"{self.start.strftime("%H:%M")} {self.summary}"

        if (
            summary_length := config.font.getlength(str(summary))
        ) and summary_length <= length:
            return summary
        ratio = length / summary_length
        for i in range(int(len(summary) * ratio)):
            if (
                new_sum := summary[: int(len(summary) * ratio) - i] + "\u2026"
            ) and config.font.getlength(new_sum) <= length:
                return new_sum
        return ""

    def _draw_background(self, img: ImageDraw, text_box: Box)->int:
        box = deepcopy(text_box)
        box.resize(5)
        img.rounded_rectangle(
            box.as_tuple(), 8, (125, 125, 255, 255),(70, 70, 125, 255)
        )
        return box.height

    def _draw_multi_day(
        self,
        config: CalConfig,
        grid: Grid,
        img: ImageDraw,
        offset_y: int = 0,
        for_day:Optional[int] = None
    )->int:
        pass

    def draw(
        self,
        config: CalConfig,
        grid: Grid,
        img: ImageDraw,
        offset_y: int = 0,
        for_day:Optional[int] = None
    ) -> int:
        coords = grid.get_coords_to_draw(self.start.day if not for_day else for_day, self.days)
        length_available_for_txt = self.days * (
            coords.p_end.x - coords.p_start.x - 2 * config.appointment_padding_px
        )
        text_shortened = self._get_summary(length_available_for_txt, config)
        text_box = Box.fromtuple(config.font.getbbox(text_shortened))
        text_box.anker_to(coords.p_start + (config.appointment_padding_px, offset_y))
        new_offset = text_box.height
        if config.draw_background:
            new_offset = self._draw_background(img, text_box)
        img.text(
            (coords.p_start + (config.appointment_padding_px, offset_y)).as_tuple(),
            text_shortened,
            config.line_ink,
            font=config.font,
        )
        # TODO: what happens when coords.p_start.y + offset-y > coords.p_end.y like too many app to show
        return new_offset

