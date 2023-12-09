from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path

import os.path, json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from PIL import Image, ImageDraw, ImageFont
from typing import Any, List, Optional, Tuple
from calendar import Calendar, monthrange, monthcalendar

import numpy as np

from enum import Enum


@dataclass
class CalConfig:
    month: int = 1
    year: int = 1970
    line_ink: Any = (0, 0, 0, 0)
    line_spacing_px: int = 10
    line_width: int = 2
    header_spacing_px: int = 150
    height: int = 1920
    width: int = 1080
    font: ImageFont.FreeTypeFont = ImageFont.truetype(
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf", 11
    )


class ORIENTATION(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class Point:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y

    def __gt__(self, other):
        return self.x > other.x and self.y > other.y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __str__(self) -> str:
        return f"Point({self.x},{self.y})"

    def __add__(self, other: int):
        if isinstance(other, int):
            return Point(self.x + other, self.y + other)
        elif isinstance(other, tuple):
            return Point(self.x + other[0], self.y + other[1])
        else:
            return Point(self.x + other.x, self.y + other.y)

    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


class Box:
    def __init__(self, p_start: Point, p_end: Point) -> None:
        assert p_start < p_end
        self.p_start = p_start
        self.p_end = p_end
        self._p2 = Point(self.p_end.x, self.p_start.y)
        self._p3 = Point(self.p_start.x, self.p_end.y)
        pass

    def is_in_box(self, p: Point):
        return p > self.p_start and p < self.p_end

    def __str__(self) -> str:
        return f"Box from {self.p_start} to {self.p_end}"

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.p_start.as_tuple() + self.p_end.as_tuple()

    def draw(self, CalConfig: CalConfig, img: ImageDraw.ImageDraw):
        to_draw = (
            self.p_start.as_tuple() + self._p2.as_tuple(),
            self.p_start.as_tuple() + self._p2.as_tuple(),
            self._p3.as_tuple() + self.p_end.as_tuple(),
            self.p_start.as_tuple() + self._p3.as_tuple(),
        )
        for points in to_draw:
            img.line(
                points,
                fill=CalConfig.line_ink,
                width=CalConfig.line_width,
            )


class Grid:
    def __init__(self, CalConfig: CalConfig) -> None:
        self._orientation = (
            ORIENTATION.HORIZONTAL
            if CalConfig.height < CalConfig.width
            else ORIENTATION.VERTICAL
        )
        self._config = CalConfig
        self._cal = np.array(monthcalendar(self._config.year, self._config.month))

    def get_coords_to_draw(self, day: int) -> Box:
        row, col = [i[0] for i in np.where(self._cal == day)]
        return self._coords_from_index(row, col)

    def _coords_from_index(self, row, col) -> Box:
        max_rows_to_draw, max_cols_to_draw = np.shape(self._cal)
        height_per_row = int(
            (self._config.height - self._config.header_spacing_px) / max_rows_to_draw
        )
        width_per_col = int(self._config.width / max_cols_to_draw)
        p_start = Point(
            width_per_col * (col),
            int(self._config.header_spacing_px + (height_per_row * (row))),
        )
        p_end = Point(
            int(p_start.x + width_per_col),
            int(p_start.y + height_per_row),
        )
        return Box(p_start, p_end)

    def draw(self, img: ImageDraw.ImageDraw):
        rows, cols = np.shape(self._cal)
        for row in range(rows):
            for col in range(cols):
                self._coords_from_index(row, col).draw(self._config, img)


class appointment:
    start: date
    end: Optional[date] = None
    summary: str = "<error>"

    def __init__(self, gcal_event) -> None:
        self._gcal_event = gcal_event

    def load(self):
        try:
            self.start = datetime.fromisoformat(
                self._gcal_event["start"]
                .get("dateTime", self._gcal_event["start"].get("date"))
                .rstrip("Z")
            )
            self.end = datetime.fromisoformat(
                str(
                    self._gcal_event["end"].get(
                        "dateTime", self._gcal_event["end"].get("date")
                    )
                ).rstrip("Z")
            )
            self.summary = self._gcal_event["summary"]
        except KeyError as exc:
            raise RuntimeError(
                f"Couldn't load appointment with given data: {self._gcal_event}"
            ) from exc

    def _get_summary(self, length: int, config: CalConfig) -> str:
        if (
            summary_length := config.font.getlength(str(self.summary))
        ) and summary_length <= length:
            return self.summary
        ratio = length / summary_length
        for i in range(int(len(self.summary) * ratio)):
            if (
                new_sum := self.summary[: int(len(self.summary) * ratio) - i] + "\u2026"
            ) and config.font.getlength(new_sum) <= length:
                return new_sum
        return ""

    def draw(
        self,
        img: ImageDraw.ImageDraw,
        grid: Grid,
        config: CalConfig,
        offset_y: int = 0,
    ) -> int:
        coords = grid.get_coords_to_draw(self.start.day)
        length_available_for_txt = (
            coords.p_end.x - coords.p_start.x - 2 * config.line_spacing_px
        )
        new_text = self._get_summary(length_available_for_txt, config)
        img.text(
            (coords.p_start + (config.line_spacing_px + offset_y)).as_tuple(),
            self._get_summary(length_available_for_txt, config),
            config.line_ink,
            font=config.font,
        )
        return config.font.getsize(new_text)[1]


class magic_day:
    appointments: List[appointment]  # holds each appointment that "crosses" the day
    pass


class magic_month:
    days = List[magic_day]

    def __init__(self, month: int, appointments: List[appointment]):
        pass

    def _draw_grid(self):
        pass

    def draw(self):
        pass


def last_day_of_month(any_day):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - datetime.timedelta(days=next_month.day)


class magic_calender(Calendar):
    month: Optional[magic_month] = None

    def __init__(self, firstweekday: int = 0, landscape: bool = False) -> None:
        self._img = Image.new(
            "RGBA",
            (GEN_WIDTH, GEN_HEIGHT) if landscape else (GEN_HEIGHT, GEN_WIDTH),
            color=(255, 255, 255, 255),
        )
        self._id = ImageDraw.Draw(self._img)
        self._creds = self.get_gcal_creds()
        super().__init__(firstweekday)

    def get_gcal_creds(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
        return creds

    def get_events(self):
        if not self._creds:
            raise RuntimeError("Credentials not loaded yet")
        try:
            service = build("calendar", "v3", credentials=self._creds)

            # Call the Calendar API
            dt_now = datetime.now()
            now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            endofmonth = monthrange(dt_now.year, dt_now.month)[1]
            print("Getting the upcoming 10 events")
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    timeMax=now,
                    maxResults=1,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

        except HttpError as error:
            print(f"An error occurred: {error}")

    def load_events_from(self, json: str):
        events = None
        self.month = magic_month(
            datetime.now().month, [appointment(event) for event in events]
        )
        pass

    def load(self, month_of_the_year: int = 0):
        self.get_events()
        pass

    def draw(self):
        self._id.line((0, 0) + self._img.size, fill=(255, 0, 0))
        self._id.line((0, self._img.size[1], self._img.size[0], 0), fill=128)
        print(vars(self))
        if self.month:
            self.month.draw()
        else:
            raise RuntimeError("month not loaded yet")

    def save(self, filepath: Path = Path("test.png")):
        self._img.save(filepath, "PNG")


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """

    cal = magic_calender(firstweekday=0)
    cal.load()
    cal.draw()
    cal.save()


if __name__ == "__main__":
    main()
