# google-calendar-hours-aggregator

Command line tool to aggregate hours from dot-separated Google Calendar event
categories. It stores configuration and OAuth tokens under
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
   - Provide a category to aggregate. For example, `ps.cp` matches
     `ps.cp.work` and `ps.cp.mtg`, but not `pscp` or `ps.cpa`.

3. The script prints each event chunk, the subtotal for every category level,
   and the total hours. For example, events in `ps.cp.mtg` and `ps.cp.work`
   produce the following subtotal tree:

   ```text
   └── ps,2.5
       └── ps.cp,2.5
           ├── ps.cp.work,1.5
           └── ps.cp.mtg,1
   ```

## Testing

Unit tests cover the event splitting and aggregation logic. After activating
the virtual environment run:

```bash
pytest
```
