from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.websockets import WebSocketDisconnect
import asyncio
import httpx
import os
import uuid

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

app = FastAPI()

users = {}
gameConnections = {}
queue = []

class AuthRequest(BaseModel):
    username: str
    password: str

class UsernameRequest(BaseModel):
    username: str


# @app.post("/register")
# async def register(req: AuthRequest):
#     if req.username in users:
#         raise HTTPException(status_code=409, detail="Username taken")
#     users[req.username] = req.password
#     return {"status": "ok"}

@app.post("/register")
async def register(req: AuthRequest):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_URL}/rest/v1/accounts",
            headers=HEADERS,
            json={"username": req.username, "password": req.password}
        )
        if res.status_code == 409:
            raise HTTPException(status_code=409, detail="Username taken")
        return {"status": "ok"}


# @app.post("/login")
# async def login(req: AuthRequest):
#     if req.username not in users or users[req.username] != req.password:
#         raise HTTPException(status_code=401, detail="Invalid credentials")
#     return {"status": "ok", "username": req.username}

@app.post("/login")
async def login(req: AuthRequest):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/accounts",
            headers=HEADERS,
            params={"username": f"eq.{req.username}", "select": "username,password"}
        )
        data = res.json()
        if not data or data[0]["password"] != req.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"status": "ok", "username": req.username}


matched = {}
sessions = {}
@app.post("/queue")
async def queuePlayer(req: UsernameRequest):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/accounts",
            headers=HEADERS,
            params={"username": f"eq.{req.username}", "select": "username"}
        )
        if not res.json():
            raise HTTPException(status_code=404, detail="Player not found")

    if req.username in queue:
        raise HTTPException(status_code=400, detail="Already queued")

    queue.append(req.username)

    if len(queue) >= 2:
        p1 = queue.pop(0)
        p2 = queue.pop(0)
        matched[p1] = p2
        matched[p2] = p1

        session_id = str(uuid.uuid4())
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{SUPABASE_URL}/rest/v1/game_sessions",
                headers=HEADERS,
                json={"id": session_id, "player1_id": p1, "player2_id": p2}
            )
        sessions[p1] = session_id
        sessions[p2] = session_id

        return {"status": "matched", "opponent": matched.get(req.username), "team": 0, "session_id": session_id}

    while req.username in queue:
        await asyncio.sleep(0.5)

    opponent = matched.get(req.username)
    return {"status": "matched", "opponent": opponent, "team": 1, "session_id": sessions.get(req.username)}


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
                await ws.send_text(data)
                await gameConnections[opponent].send_text(data)
    except WebSocketDisconnect:
        gameConnections.pop(username)