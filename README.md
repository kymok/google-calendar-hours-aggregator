# google-calendar-hours-aggregator

Command line tool to aggregate hours from Google Calendar events matching a
given title. It stores configuration and OAuth tokens under
`~/.gcal-hours-aggregator`.

## Setup

The project uses [uv](https://github.com/astral-sh/uv) for dependency
management. After installing `uv` on your system run:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Usage

1. Run the script:

   ```bash
   python gcal_hours_aggregator.py
   ```

2. Follow the interactive prompts:
   - Enter your Google account name.
   - Select a calendar using the arrow keys.
   - Choose the month to aggregate.
   - Provide a string that should be contained in the event title.

3. The script prints the total hours and a CSV table of each event chunk.

## Testing

Unit tests cover the event splitting and aggregation logic. After activating
the virtual environment run:

```bash
pytest
```
