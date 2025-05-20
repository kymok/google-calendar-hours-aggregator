# google-calendar-hours-aggregator

Command line tool to aggregate hours from Google Calendar events matching a
given title. It stores configuration and OAuth tokens under
`~/.gcal-hours-aggregator`.

## Setup

### Install dependencies

```
uv venv
source .venv/bin/activate
uv sync
```

### Get OAuth client secret

Create a Google Cloud project and create a OAuth client secret with permissions `.../auth/calendar.readonly` and `.../auth/calendar.events.readonly`.

## Usage

1. Run the script:

   ```bash
   python3 gcal_hours_aggregator.py
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
