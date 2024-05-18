from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, date, time
from pathlib import Path

import os.path, pytz

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from PIL import Image, ImageDraw, ImageFont
from typing import Any, List, Optional, Set, Tuple, overload
from calendar import Calendar, monthrange, monthcalendar

from enum import Enum


@dataclass
class CalConfig:
    month: int = date.today().month
    year: int = date.today().year
    line_ink: Any = (0, 0, 0, 0)
    line_spacing_px: int = 20
    day_spacing_px: int = 15
    line_width: int = 2
    header_spacing_px: int = 350
    height: int = 1920
    width: int = 1080
    font: ImageFont.FreeTypeFont = ImageFont.truetype(
        "arial.ttf"
        if "nt" in os.name.lower()
        else "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        11,
    )


class ORIENTATION(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


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

    def draw(self, CalConfig: CalConfig, img: ImageDraw.ImageDraw):
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

    def get_coords_to_draw(self, day: int) -> Box:
        row, col = self._where(day)
        return self._coords_from_index(row, col)

    def _get_dimensions(self) -> Tuple[int, int]:
        return max(
            [
                (row, col)
                for row, x in enumerate(self._cal, 1)
                for col, _ in enumerate(x, 1)
            ]
        )

    def _coords_from_index(self, row, col) -> Box:
        max_rows_to_draw, max_cols_to_draw = self._get_dimensions()
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
        rows, cols = self._get_dimensions()
        for row in range(rows):
            for col in range(cols):
                self._coords_from_index(row, col).draw(self._config, img)


class appointment:
    start: datetime
    end: datetime
    id: str
    summary: str = "<error>"

    def __init__(self, gcal_event) -> None:
        self._gcal_event = gcal_event
        self.load()

    def __str__(self) -> str:
        return f"{self.start.isoformat()} - { self.end.isoformat() }: {self.summary}"

    def __eq__(self, __o: object) -> bool:
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
        if (
            (days := (self.end.date() - self.start.date()).days)
            and days > 0
            and self.end.time() != time(0, 0)
        ):
            return days + 1
        else:
            return 1

    @property
    def multiday(self) -> bool:
        return not self.start.date() == self.end.date()

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

    def _draw_background(self, img: ImageDraw.ImageDraw, text_box: Box):
        box = deepcopy(text_box)
        box.resize(5)
        img.rounded_rectangle(
            box.as_tuple(), 8, (125, 125, 255, 255), (125, 125, 255, 255)
        )

    def draw(
        self,
        config: CalConfig,
        grid: Grid,
        img: ImageDraw.ImageDraw,
        offset_y: int = 0,
    ) -> int:
        coords = grid.get_coords_to_draw(self.start.day)
        length_available_for_txt = self.days * (
            coords.p_end.x - coords.p_start.x - 2 * config.line_spacing_px
        )
        text_shortened = self._get_summary(length_available_for_txt, config)
        text_box = Box.fromtuple(config.font.getbbox(text_shortened))
        text_box.anker_to(coords.p_start + (config.line_spacing_px, offset_y))
        self._draw_background(img, text_box)
        img.text(
            (coords.p_start + (config.line_spacing_px, offset_y)).as_tuple(),
            text_shortened,
            config.line_ink,
            font=config.font,
        )
        # TODO: what happens when coords.p_start.y + offset-y > coords.p_end.y like too many app to show
        return text_box.height


class magic_day:
    def __init__(
        self, day: int, appointments: Set[appointment], config: CalConfig
    ) -> None:
        self._appointments = [
            a
            for a in appointments
            if a.start
            <= datetime(config.year, config.month, day, tzinfo=pytz.UTC)
            < a.end
        ]
        self._appointments.sort()
        self._day = day

    def _get_day_color(self, config: CalConfig, grid: Grid):
        if date.today().day == self._day:
            return (255, 255, 255, 255)
        else:
            return (
                config.line_ink if not grid.is_weekend(self._day) else (255, 0, 0, 255)
            )

    def _draw_circle(
        self, img: ImageDraw.ImageDraw, point_text: Point, bounding_box: Box
    ):
        if date.today().day == self._day:
            box = bounding_box.encapsulating_square()
            box.anker_to(point_text)
            img.ellipse(box.as_tuple(), fill=(255, 0, 0, 255))

    def draw(self, config: CalConfig, grid: Grid, img: ImageDraw.ImageDraw):
        coords = grid.get_coords_to_draw(self._day)
        font = config.font.font_variant(size=56)
        bounding_box = Box.fromtuple(font.getbbox(str(self._day)))
        _offset_x = (
            coords.p_end.x
            - coords.p_start.x
            - (bounding_box.p_end.x - bounding_box.p_start.x)
        ) / 2
        _offset_y = bounding_box.p_end.y
        coords_to_draw = coords.p_start + (_offset_x, 0)
        self._draw_circle(img, coords_to_draw, bounding_box + 5)
        img.text(
            coords_to_draw.as_tuple(),
            f"{self._day}",
            font=font,
            fill=self._get_day_color(config, grid),
        )
        for app in self._appointments:
            _offset_y += config.line_spacing_px
            _offset_y += app.draw(config, grid, img, _offset_y)
            print(_offset_y)


class magic_month:
    def __init__(self, config: CalConfig, grid: Grid, appointments: List[appointment]):
        self._month = config.month
        self.days = []
        for week in grid._cal:
            for day in week:
                if day != 0:
                    self.days.append(magic_day(day, appointments, config))

    def _get_header_text_size(self, config: CalConfig) -> int:
        diff = 2
        font_size = 1
        while diff > 1:
            font_size = int(font_size + diff / 2)
            font = config.font.font_variant(size=int(font_size + diff / 2))
            box = Box.fromtuple(font.getbbox(str(self._month)))
            diff = config.header_spacing_px - box.p_end.y

        return font_size

    def draw(self, config: CalConfig, grid: Grid, img: ImageDraw.ImageDraw):
        font = config.font.font_variant(size=self._get_header_text_size(config))
        box = Box.fromtuple(font.getbbox(str(self._month)))
        p = Point(
            int((config.width / 2) - box.width / 2),
            -int(box.p_start.y / 2),  # might not work with different fonts
        )
        img.text(
            p.as_tuple(),
            str(self._month),
            config.line_ink,
            font=font,
        )
        # img.point(p.as_tuple(), (255, 0, 0))
        for day in self.days:
            day.draw(config, grid, img)


class magic_calender(Calendar):
    month: Optional[magic_month] = None

    def __init__(self, config: CalConfig = CalConfig(), firstweekday: int = 0) -> None:
        self._img = Image.new(
            "RGBA",
            (config.width, config.height),
            color=(255, 255, 255, 255),
        )
        self._id = ImageDraw.Draw(self._img)
        self._config = config
        self._grid = Grid(config)
        super().__init__(firstweekday)

    def get_gcal_creds(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if (cred_path := Path("token.json")) and cred_path.is_file():
            creds = Credentials.from_authorized_user_file(cred_path, SCOPES)
            # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    print("Token expired! Please restart")
                    cred_path.unlink()

            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        Path.cwd() / "credentials.json", SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    # Save the credentials for the next run
                    with open("token.json", "w") as token:
                        token.write(creds.to_json())
                except FileNotFoundError:
                    print(
                        "Couldn't find credentials.json in working dir! Consider creating it here: TODO link"
                    )
        return creds

    def get_events_api(self) -> List[Any]:
        _creds = self.get_gcal_creds()
        if not _creds:
            raise RuntimeError("Credentials not loaded yet")
        try:
            service = build("calendar", "v3", credentials=_creds)

            # Call the Calendar API
            now = (
                datetime.combine(
                    date(self._config.year, self._config.month, 1), datetime.min.time()
                ).isoformat()
                + "Z"
            )  # 'Z' indicates UTC time 2023-12-23T20:21:21.096973Z
            last_day_of_month = monthrange(self._config.year, self._config.month)[1]
            ldam = (
                datetime.combine(
                    date(self._config.year, self._config.month, last_day_of_month),
                    datetime.max.time(),
                ).isoformat()
                + "Z"
            )  # 'Z' indicates UTC time
            page_token = None
            events = []
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            while True:
                for calendar_list_entry in calendar_list["items"]:
                    print(calendar_list_entry["id"])
                    print("Getting the upcoming events")
                    events_result = (
                        service.events()
                        .list(
                            calendarId=calendar_list_entry["id"],
                            timeMin=now,
                            timeMax=ldam,
                            # maxResults=1,
                            singleEvents=True,
                            orderBy="startTime",
                        )
                        .execute()
                    )
                    events += events_result.get("items", [])
                page_token = calendar_list.get("nextPageToken")
                if not page_token:
                    break

            return events

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def load(self, events: Optional[List] = None):
        _events = self.get_events_api() if not events else events
        self.month = magic_month(
            self._config,
            self._grid,
            list(set([appointment(event) for event in _events])),
        )

    def draw(self):
        self._grid.draw(self._id)
        if self.month:
            self.month.draw(self._config, self._grid, self._id)
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
    try:
        cal = magic_calender(firstweekday=0)
        cal.load()
        cal.draw()
        cal.save(f"{date.today().isoformat()}.png")
    except RuntimeError as exc:
        print(f"An error occurred: {exc}")


if __name__ == "__main__":
    main()
