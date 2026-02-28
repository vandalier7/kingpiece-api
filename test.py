
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.websockets import WebSocketDisconnect
import asyncio

app = FastAPI()

users = {} # username: password
gameConnections = {}
queue = []

class AuthRequest(BaseModel):
    username: str
    password: str

class UsernameRequest(BaseModel):
    username: str


@app.post("/register")
async def register(req: AuthRequest):
    if req.username in users:
        raise HTTPException(status_code=409, detail="Username taken")
    users[req.username] = req.password
    return {"status": "ok"}

@app.post("/login")
async def login(req: AuthRequest):
    if req.username not in users or users[req.username] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "ok", "username": req.username}


matched = {}
@app.post("/queue")
async def queuePlayer(req: UsernameRequest):
    if req.username not in users:
        raise HTTPException(status_code=404, detail="Player not found")

    if req.username in queue:
        raise HTTPException(status_code=400, detail="Already queued")

    
    queue.append(req.username)

    if len(queue) >= 2:
        p1 = queue.pop(0)
        p2 = queue.pop(0)
        matched[p1] = p2
        matched[p2] = p1
        return {"status": "matched", "opponent": matched.pop(req.username), "team": 0}

    while req.username in queue:
        await asyncio.sleep(0.5)

    opponent = matched.pop(req.username)
    return {"status": "matched", "opponent": opponent, "team": 1}

@app.websocket("/game")
async def game(ws: WebSocket):
    await ws.accept()
    username = ws.query_params["username"]
    gameConnections[username] = ws
    
    try:
        while True:
            data = await ws.receive_text()
            opponent = matched.get(username)
            if opponent and opponent in gameConnections:
                await gameConnections[opponent].send_text(data)
                await ws.send_text(data)
    except WebSocketDisconnect:
        gameConnections.pop(username)