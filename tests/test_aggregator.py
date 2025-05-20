import datetime
from gcal_hours_aggregator import split_event_into_days, aggregate_hours, EventChunk


def test_split_single_day():
    start = datetime.datetime(2025, 5, 1, 18, 0)
    end = datetime.datetime(2025, 5, 1, 19, 30)
    chunks = split_event_into_days(start, end)
    assert chunks == [EventChunk(year=2025, month=5, day=1, start=18.0, end=19.5, hours=1.5)]


def test_split_multi_day():
    start = datetime.datetime(2025, 5, 1, 23, 0)
    end = datetime.datetime(2025, 5, 2, 1, 0)
    chunks = split_event_into_days(start, end)
    assert len(chunks) == 2
    assert chunks[0].hours == 1
    assert chunks[1].hours == 1


def test_aggregate_hours():
    events = [
        {
            'summary': 'Work',
            'start': {'dateTime': '2025-05-01T18:00:00Z'},
            'end': {'dateTime': '2025-05-01T19:30:00Z'},
        },
        {
            'summary': 'Play',
            'start': {'dateTime': '2025-05-01T20:00:00Z'},
            'end': {'dateTime': '2025-05-01T21:00:00Z'},
        }
    ]
    chunks = aggregate_hours(events, 'Work')
    assert len(chunks) == 1
    assert chunks[0].hours == 1.5
