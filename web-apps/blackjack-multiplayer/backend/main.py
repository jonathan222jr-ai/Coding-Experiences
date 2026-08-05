from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from auth import router as auth_router
from games import router as games_router
import socketio
import game_socket

# --- Socket.IO server ---
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
app = FastAPI()
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Create tables ---
Base.metadata.create_all(bind=engine)

# --- Routers ---
app.include_router(auth_router, prefix="/auth")
app.include_router(games_router, prefix="/api")

# --- Attach socket handlers ---
game_socket.attach_handlers(sio)
