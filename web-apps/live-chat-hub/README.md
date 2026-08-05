# Live Chat Hub

Multi-user web chat built on Flask and Socket.IO, with account registration and login.

## Stack

Flask · Flask-SocketIO · Flask-SQLAlchemy · SQLite · Jinja templates

## Notes on the implementation

- Passwords are never stored in plaintext — they go through Werkzeug's
  `generate_password_hash` (scrypt) and are verified with `check_password_hash`.
- Messages are pushed over a Socket.IO connection rather than polled.
- `SECRET_KEY` is read from the environment, falling back to a development value.
  Set a real one before running this anywhere but locally.

## Running it

```bash
pip install -r requirements.txt
export SECRET_KEY="a-real-random-secret"
python app.py
```

The SQLite database is created on first run and is deliberately not committed.
