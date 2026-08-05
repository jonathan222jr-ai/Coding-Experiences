from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Game, GamePlayer, User
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreateGameRequest(BaseModel):
    name: str
    user_id: int

@router.get("/games")
def list_games(db: Session = Depends(get_db)):
    games = db.query(Game).all()
    return {
        "games": [
            {
                "id": g.id,
                "name": g.name,
                "created_at": g.created_at.isoformat(),
                "players": [{"username": gp.user.username} for gp in g.players]
            }
            for g in games
        ]
    }

@router.post("/games")
def create_game(req: CreateGameRequest, db: Session = Depends(get_db)):
    game = Game(name=req.name)
    db.add(game)
    db.commit()
    db.refresh(game)

    gp = GamePlayer(game_id=game.id, user_id=req.user_id)
    db.add(gp)
    db.commit()

    return {"id": game.id}
