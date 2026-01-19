from __future__ import annotations


from datetime import datetime, date
from pathlib import Path
from calendar import Calendar, monthrange
from typing import Any, List, Optional, Set

import pytz

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from PIL import Image, ImageDraw


from magic_calender.core.appointment import Appointment
from magic_calender.core.point import Point
from magic_calender.core.grid import Grid
from magic_calender.core.box import Box
from magic_calender.config import CalConfig




class MagicDay:
    def __init__(
        self, day: int, appointments: Set[Appointment], config: CalConfig
    ) -> None:
        self._appointments = [
            a
            for a in appointments
            if a.on_day(datetime(config.year, config.month, day, tzinfo=pytz.UTC))
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
    ) -> int:
        if date.today().day == self._day:
            box = bounding_box.encapsulating_square()
            box.anker_to(point_text)
            img.ellipse(box.as_tuple(), fill=(255, 0, 0, 255))
            return box.p_end.y - box.p_start.y
        return 0

    def draw(self, config: CalConfig, grid: Grid, img: ImageDraw.ImageDraw):
        coords = grid.get_coords_to_draw(self._day)
        font = config.font.font_variant(size=config.number_size)
        bounding_box = Box.fromtuple(font.getbbox(str(self._day)))
        _offset_x = (
            coords.p_end.x
            - coords.p_start.x
            - (bounding_box.p_end.x - bounding_box.p_start.x)
        ) / 2
        _offset_y = bounding_box.p_end.y + config.day_spacing_px
        coords_to_draw = coords.p_start + (_offset_x, 0)
        _offset_y = max(_offset_y,self._draw_circle(img, coords_to_draw, bounding_box + 5))
        img.text(
            coords_to_draw.as_tuple(),
            f"{self._day}",
            font=font,
            fill=self._get_day_color(config, grid),
        )
        for app in self._appointments:
            _offset_y += config.appointment_spacing_px
            _offset_y += app.draw(config, grid, img, _offset_y,self._day)

class MagicMonth:
    def __init__(self, config: CalConfig, grid: Grid, appointments: List[Appointment]):
        self._month = config.month
        self.days = []
        for week in grid._cal:
            for day in week:
                if day != 0:
                    self.days.append(MagicDay(day, appointments, config))

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


class MagicCalender(Calendar):
    month: Optional[MagicMonth] = None

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
                    flow = Flow.from_client_secrets_file(
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
        events_cleaned = set([Appointment(event) for event in _events])
        self.month = MagicMonth(
            self._config,
            self._grid,
            list(events_cleaned),
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
