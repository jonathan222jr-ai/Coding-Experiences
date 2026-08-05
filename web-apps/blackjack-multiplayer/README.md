# Multiplayer Blackjack

Real-time multiplayer Blackjack — CSE 108 final project. Players register, join a
shared lobby, and play a synchronized hand against each other.

## Stack

**Backend** — FastAPI · Socket.IO (`python-socketio`) · SQLAlchemy · SQLite
**Frontend** — vanilla HTML/CSS/JavaScript, no framework

## Structure

```
backend/
  main.py         # FastAPI app, CORS, mounts the Socket.IO ASGI server
  auth.py         # registration and login routes
  models.py       # User, Game, GamePlayer
  database.py     # engine and session setup
  games.py        # game lifecycle REST routes
  game_socket.py  # Socket.IO event handlers — the real-time game loop
frontend/
  index.html
  js/             # login, signup, lobby, and game screens
  api/api.js      # fetch wrappers for the backend
  css/style.css
```

The interesting part is the split between `games.py` and `game_socket.py`: REST handles
creating and listing games, while turn-by-turn play runs over Socket.IO so every player
sees the same table state as it changes.

## Running it

```bash
cd backend
pip install -r requirements.txt
uvicorn main:socket_app --reload
```

Then serve the `frontend/` directory and open it in a browser.

The SQLite database is created on first run and is not committed.
