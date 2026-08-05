import socketio
import random

rooms = {}

def new_game_state():
    return {
        "status": "waiting",
        "players": {},
        "dealer": {"hand": []},
        "chat": []
    }

def draw_card():
    ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
    suits = ["♠","♥","♦","♣"]
    return {"r": random.choice(ranks), "s": random.choice(suits)}

def attach_handlers(sio: socketio.AsyncServer):

    @sio.event
    async def connect(sid, environ):
        print("Client connected:", sid)

    @sio.event
    async def join_game(sid, data):
        game_id = data["gameId"]
        if game_id not in rooms:
            rooms[game_id] = new_game_state()
        game = rooms[game_id]
        game["players"][sid] = {
            "username": f"Player-{sid[:4]}",
            "hand": [],
            "bet": 0,
            "balance": 100,
            "status": "joined"
        }
        await sio.enter_room(sid, f"game_{game_id}")
        await sio.emit("game_state", game, room=f"game_{game_id}")

    @sio.event
    async def chat(sid, data):
        game_id = data["gameId"]
        msg = {"user": f"Player-{sid[:4]}", "text": data["text"]}
        rooms[game_id]["chat"].append(msg)
        await sio.emit("chat", msg, room=f"game_{game_id}")

    @sio.event
    async def hit(sid, data):
        game_id = data["gameId"]
        card = draw_card()
        rooms[game_id]["players"][sid]["hand"].append(card)
        await sio.emit("game_state", rooms[game_id], room=f"game_{game_id}")

    @sio.event
    async def stand(sid, data):
        pass

    @sio.event
    async def disconnect(sid):
        print("Client disconnected:", sid)
