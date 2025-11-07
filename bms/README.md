# Banking Management System (BMS) - Minimal Backend

Small Flask + SQLAlchemy backend for managing accounts. Includes:
- CRUD API for accounts (POST/GET/PUT/DELETE)
- Simple emailer (sync + background)
- Batch balance calculators (threaded + async)
- Minimal CLI for manual requests
- Pytest unit tests for core logic

Prerequisites
- Python 3.10+ (3.11/3.12 recommended)
- Virtual environment (recommended)
- Dependencies: see requirements.txt or install minimal set:
  pip install flask sqlalchemy requests beautifulsoup4 pytest

Quick setup (Windows PowerShell)
1. From project package root:
   cd "G:\Banking-Management-System\bms"

2. Create & activate venv:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

3. Install deps:
   pip install -r requirements.txt
   (or) pip install flask sqlalchemy pytest requests beautifulsoup4

Run the app
1. Start the Flask app:
   python run.py
   The API base is: http://127.0.0.1:5000/api/v1

2. Use the provided CLI or HTTP client (curl / Postman) to hit endpoints:
   python client\cli.py create Alice A001 100
   python client\cli.py list

Emailer (development)
- By default the app/emailer prefers a local SMTP debug server (localhost:1025).
- For dev inspect emails by running a debug SMTP server:
  python -m aiosmtpd -n -l localhost:1025
- Or provide mailer config at `mailer/config.py` with:
  smtp_host, smtp_port, username (optional), app_password, from_address, tp_address, use_tls

Run tests
- From package root (bms) run:
  pytest -q

What to check after setup
- Create/list/get/update/delete accounts via API or CLI.
- employee_app_logs.log for app logs.
- Batch calc functions from REPL or tests.
- Email output on SMTP debug server if enabled.

Project layout (key files)
- app/             (Flask app package)
  - __init__.py    (create_app)
  - crud.py        (business logic)
  - models.py      (SQLAlchemy models)
  - db.py          (engine/session factory)
  - emailer.py     (sync + background send)
  - batch_calc.py  (threaded / async batch sums)
  - routes.py      (API routes)
- client/cli.py    (very small CLI)
- tests/           (pytest test_crud.py, test_batch_calc.py)
- run.py           (start the server)
- mailer/config.py (optional local mail settings)

Keep it simple: run the server, create a few accounts, run tests. If you need a README expanded with examples or deployment notes, say which section to expand.