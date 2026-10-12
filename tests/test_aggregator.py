import datetime
from main import (
    EventChunk,
    aggregate_hours,
    category_subtotals,
    category_tree_lines,
    get_local_timezone,
    split_event_into_days,
)


def test_split_single_day():
    local_tz = get_local_timezone()
    start = datetime.datetime(2025, 5, 1, 18, 0, tzinfo=local_tz)
    end = datetime.datetime(2025, 5, 1, 19, 30, tzinfo=local_tz)
    chunks = split_event_into_days(start, end)
    assert chunks == [EventChunk(year=2025, month=5, day=1, start=18.0, end=19.5, hours=1.5)]


def test_split_multi_day():
    local_tz = get_local_timezone()
    start = datetime.datetime(2025, 5, 1, 23, 0, tzinfo=local_tz)
    end = datetime.datetime(2025, 5, 2, 1, 0, tzinfo=local_tz)
    chunks = split_event_into_days(start, end)
    assert len(chunks) == 2
    assert chunks[0].hours == 1
    assert chunks[1].hours == 1


def test_aggregate_hours():
    events = [
        {
            'summary': 'ps.cp.work',
            'start': {'dateTime': '2025-05-01T18:00:00+09:00'},
            'end': {'dateTime': '2025-05-01T19:30:00+09:00'},
        },
        {
            'summary': 'ps.cp.mtg',
            'start': {'dateTime': '2025-05-01T20:00:00+09:00'},
            'end': {'dateTime': '2025-05-01T21:00:00+09:00'},
        },
        {
            'summary': 'pscp',
            'start': {'dateTime': '2025-05-01T21:00:00+09:00'},
            'end': {'dateTime': '2025-05-01T22:00:00+09:00'},
        },
        {
            'summary': 'ps.cpa',
            'start': {'dateTime': '2025-05-01T22:00:00+09:00'},
            'end': {'dateTime': '2025-05-01T23:00:00+09:00'},
        },
    ]
    chunks = aggregate_hours(events, 'ps.cp')

    assert [(chunk.category, chunk.hours) for chunk in chunks] == [
        ('ps.cp.work', 1.5),
        ('ps.cp.mtg', 1),
    ]
    assert category_subtotals(chunks) == {
        'ps': 2.5,
        'ps.cp': 2.5,
        'ps.cp.work': 1.5,
        'ps.cp.mtg': 1,
    }
    assert category_tree_lines(category_subtotals(chunks)) == [
        '└── ps,2.5',
        '    └── ps.cp,2.5',
        '        ├── ps.cp.work,1.5',
        '        └── ps.cp.mtg,1',
    ]
