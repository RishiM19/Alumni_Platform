# Aegis Alumni Platform

Day-one backend foundation for desktop, mobile and developer API work. Run this scaffold locally with synthetic records. Its public fixture credentials and in-memory fixture reads are for development. Production identity and persistence are later integration steps.

## Start the API

Run these from the repository root using Python 3.11 or newer.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r api/requirements-dev.txt
python -m uvicorn api.main:app --reload
```

Open http://127.0.0.1:8000/docs for the API reference, or run the sample request.

```sh
curl -H 'Authorization: Bearer demo-campus-a' \
  'http://127.0.0.1:8000/api/v1/alumni?q=climate'
python -m pytest -q
```

## Antigravity handoff

Build client UI in `apps/desktop/` and `apps/mobile/` on a separate branch. Use `contracts/openapi.json` for the implemented directory reads and `fixtures/` for synthetic records, roster and update examples. The development token `demo-campus-a` sees the first two profiles. `demo-campus-b` sees the third. Keep fixture credentials in development configuration.

Start the directory and profile screens against the API. Build sign-in, CSV upload, proposal submission and the review queue as isolated mock states until their endpoints are agreed. Keep database changes, contract edits and root configuration with the backend owner. Report the commit, checks run, and any contract change needed at handoff.
