import pytest
import json
from datetime import datetime
from .. import magic_calender as mc
import pytz


def test_magic_appointment_load(example_json):
    ap = mc.appointment(example_json[0])
    assert ap.start == datetime.fromisoformat("2023-12-06").replace(tzinfo=pytz.UTC)
    assert ap.end == datetime.fromisoformat("2023-12-07T06:09:23").replace(
        tzinfo=pytz.UTC
    )
    assert ap.summary == "Example event"
    assert ap.multiday


def test_magic_appointment_load_fails():
    example_json = json.loads(
        '{"start": {"date": "2023-12-05"}, "end":{"dateTime": "2023-12-06T06:09:23Z" }, "summary": "Example event", "id":"hash1234"}'
    )
    ap = mc.appointment(example_json)
    assert ap.start == datetime.fromisoformat("2023-12-05").replace(tzinfo=pytz.UTC)
    assert ap.end == datetime.fromisoformat("2023-12-06T06:09:23").replace(
        tzinfo=pytz.UTC
    )
    assert ap.summary == "Example event"


def test_magic_appointment_text_cut(example_json, example_config):
    ap = mc.appointment(example_json[0])
    example_config.width = 110
    example_config.line_spacing_px = 10
    ap.summary = "This text should be longer than 100px"
    length = example_config.font.getlength(ap.summary)
    assert length > 100


#   short = ap._get_summary(100, example_config)
#   assert short == ap.summary[:13] + "\u2026"


def test_magic_appointment_draw(example_json, example_img, example_config):
    ap = mc.appointment(example_json[0])
    ap.summary = "Long Example Event Summary"
    grid = mc.Grid(example_config)
    grid.draw(example_img)
    assert 13 == ap.draw(example_config, grid, example_img, 50)
