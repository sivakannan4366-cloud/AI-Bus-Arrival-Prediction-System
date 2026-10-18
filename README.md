# Mini RedBus AI Project

Flask, SQLite, and scikit-learn demo for bus arrival prediction and booking.

## Setup (Windows PowerShell)

Python 3.7.0 is currently installed on this machine; the pinned packages below support this older patch release.

```powershell
py -3.7 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. Settings are read from `.env` by [config.py](config.py).
The database and training CSV are resolved relative to this project, so the app can
also be launched from another current directory. Edit `.env` to change the port,
host, debug mode, database path, or local secret key. Copy `.env.example` when
setting up another checkout. Flask creates or upgrades the SQLite database at startup.

## Optional Twilio alerts

Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and either `TWILIO_WHATSAPP_FROM`
or `TWILIO_SMS_FROM` in `.env`. Alerts are sent only after the passenger selects
the booking alert opt-in.
