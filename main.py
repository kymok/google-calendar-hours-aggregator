
import os
import json
import datetime
import pickle
from dataclasses import dataclass
from typing import List, Optional

try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except Exception:
    build = InstalledAppFlow = Request = None  # type: ignore

CONFIG_DIR = os.path.expanduser("~/.gcal-hours-aggregator")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

@dataclass
class EventChunk:
    year: int
    month: int
    day: int
    start: float
    end: float
    hours: float

def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)


def load_config() -> dict:
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    ensure_config_dir()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def authenticate(account: str):
    """Authenticate with Google and return a Calendar service."""
    creds = None
    token_path = os.path.join(CONFIG_DIR, f'{account}_token.pickle')
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            if InstalledAppFlow is None:
                raise RuntimeError("Google API libraries are not available")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    if build is None:
        raise RuntimeError("Google API libraries are not available")
    service = build('calendar', 'v3', credentials=creds)
    return service


def split_event_into_days(start: datetime.datetime, end: datetime.datetime) -> List[EventChunk]:
    """Split events that span multiple days into daily chunks."""
    chunks: List[EventChunk] = []
    current = start
    while current.date() < end.date():
        next_midnight = datetime.datetime.combine(
            current.date() + datetime.timedelta(days=1),
            datetime.time.min,
            tzinfo=current.tzinfo
        )
        hours = (next_midnight - current).total_seconds() / 3600
        chunks.append(EventChunk(
            year=current.year,
            month=current.month,
            day=current.day,
            start=current.hour + current.minute / 60,
            end=24.0,
            hours=hours
        ))
        current = next_midnight
    hours = (end - current).total_seconds() / 3600
    chunks.append(EventChunk(
        year=current.year,
        month=current.month,
        day=current.day,
        start=current.hour + current.minute / 60,
        end=end.hour + end.minute / 60 + end.second / 3600,
        hours=hours
    ))
    return chunks


def aggregate_hours(events: List[dict], title_filter: str) -> List[EventChunk]:
    chunks: List[EventChunk] = []
    for ev in events:
        summary = ev.get('summary', '')
        if title_filter not in summary:
            continue
        start = ev['start'].get('dateTime') or ev['start'].get('date') + 'T00:00:00Z'
        end = ev['end'].get('dateTime') or ev['end'].get('date') + 'T00:00:00Z'
        start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
        chunks.extend(split_event_into_days(start_dt, end_dt))
    return chunks


def total_hours(chunks: List[EventChunk]) -> float:
    return sum(c.hours for c in chunks)


def add_month(date: datetime.date, delta: int) -> datetime.date:
    """Return date moved delta months forward or backward."""
    year = date.year + (date.month - 1 + delta) // 12
    month = (date.month - 1 + delta) % 12 + 1
    return datetime.date(year, month, 1)


def select_from_list(options: List[str], title: str, default: Optional[str] = None) -> str:
    """Simple arrow-key selection using curses."""
    import curses

    def menu(stdscr):
        # カラー設定の初期化
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, -1)  # 通常テキスト用
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # 選択項目用

        curses.curs_set(0)
        pos = options.index(default) if default in options else 0
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, title, curses.color_pair(1))
            for idx, opt in enumerate(options):
                if idx == pos:
                    # 選択中の項目は反転表示
                    stdscr.addstr(idx + 2, 0, "> " + opt, curses.color_pair(2))
                else:
                    # 非選択項目は通常表示
                    stdscr.addstr(idx + 2, 0, "  " + opt, curses.color_pair(1))
            key = stdscr.getch()
            if key == curses.KEY_UP and pos > 0:
                pos -= 1
            elif key == curses.KEY_DOWN and pos < len(options) - 1:
                pos += 1
            elif key in (curses.KEY_ENTER, ord('\n')):
                return options[pos]
    return curses.wrapper(menu)


def select_month(default: datetime.date) -> datetime.date:
    import curses

    def inc_month(date: datetime.date, delta: int) -> datetime.date:
        year = date.year + (date.month - 1 + delta) // 12
        month = (date.month - 1 + delta) % 12 + 1
        return datetime.date(year, month, 1)

    def menu(stdscr):
        # カラー設定の初期化
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, -1)  # 通常テキスト用
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # 選択項目用

        curses.curs_set(0)
        current = default
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Select month (LEFT/RIGHT to change, ENTER to confirm):", curses.color_pair(1))
            stdscr.addstr(1, 0, current.strftime('%Y-%m'), curses.color_pair(2))
            key = stdscr.getch()
            if key == curses.KEY_LEFT:
                current = inc_month(current, -1)
            elif key == curses.KEY_RIGHT:
                current = inc_month(current, 1)
            elif key in (curses.KEY_ENTER, ord('\n')):
                return current
    return curses.wrapper(menu)


def main():
    config = load_config()
    account = input(f"Google account name ({config.get('account', '')}): ") or config.get('account')
    if not account:
        print('Account name is required.')
        return
    config['account'] = account
    service = authenticate(account)

    # Select calendar
    calendar_list = service.calendarList().list().execute()
    calendars = [item['summary'] for item in calendar_list.get('items', [])]
    default_summary = None
    if 'calendar' in config:
        for item in calendar_list.get('items', []):
            if item['id'] == config['calendar']:
                default_summary = item['summary']
                break
    cal_summary = select_from_list(calendars, "Select calendar:", default_summary)
    calendar_id = next(item['id'] for item in calendar_list['items'] if item['summary'] == cal_summary)
    config['calendar'] = calendar_id
    print(f"Calendar: {cal_summary}")

    # Select month
    today = datetime.date.today().replace(day=1)
    default_month = today
    if 'month' in config:
        try:
            default_month = datetime.datetime.strptime(config['month'], '%Y-%m').date()
        except ValueError:
            default_month = today
    month = select_month(default_month)
    config['month'] = month.strftime('%Y-%m')
    print(f"Month: {month.strftime('%Y-%m')}")

    save_config(config)

    title_filter = input('Event title contains: ')

    start_date = month
    end_date = add_month(month, 1)

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_date.isoformat() + 'T00:00:00Z',
        timeMax=end_date.isoformat() + 'T00:00:00Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    chunks = aggregate_hours(events, title_filter)
    total = total_hours(chunks)
    
    
    print('year,month,day,start,end,hours')
    for c in chunks:
        print(f"{c.year},{c.month:02d},{c.day:02d},{c.start:g},{c.end:g},{c.hours:g}")
    print('----')
    print(f'Total Hours: {total:.2f} hours')

if __name__ == '__main__':
    main()
