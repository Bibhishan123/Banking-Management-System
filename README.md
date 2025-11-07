# Banking Management System (BMS) — Simple README

Minimal Flask + SQLAlchemy backend for managing accounts.

Important highlights
- **Quick to run:** start server with `python run.py` and use the CLI or curl to hit endpoints.
- **Tests ready:** run `pytest -q` from the `bms` folder.
- **Email dev-friendly:** use a local SMTP debug server (`python -m aiosmtpd -n -l localhost:1025`) or add `mailer/config.py` for real SMTP.
- **Database:** uses SQLite by default (`db.sqlite`). Tests use an in-memory DB.

Quick start (Windows PowerShell)
1. Open project folder:
   cd "G:\Banking-Management-System\bms"

2. Create & activate venv:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

3. Install required packages:
   pip install flask sqlalchemy pytest requests beautifulsoup4

Run the app
- Start the server:
  `python run.py`  
- API base: `http://127.0.0.1:5000/api/v1`  
- Use the CLI:
  `python client\cli.py create Alice A001 100`

Run tests
- From the `bms` folder:
  `pytest -q`

Quick email dev check
- Start debug SMTP server:
  `python -m aiosmtpd -n -l localhost:1025`
- Create an account (server running) and watch the SMTP terminal for the message.

Notes
- Logs are written to `employee_app_logs.log` in the project root.
- If you need more examples (curl commands, CI, Docker), say which section to expand.