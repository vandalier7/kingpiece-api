
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

app = FastAPI()

class Pair:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    


connections = []
pairs = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    try:
        await broadcast(ws, {"type": "notif", "payload": "Connected!"})
    except WebSocketDisconnect:
        connections.remove(ws)
    
    try:
        while True:
            data = await ws.receive_text()
            for socket in connections:
                await broadcast(socket, data)
    except WebSocketDisconnect:
        connections.remove(ws)

async def broadcast(socket: WebSocket, data: str):
    await socket.send_text(f"{data}")

def onConnect(socket: WebSocket):
    if len(connections) < 2:
        return
    foundPair = None
    for s in connections:
        if s == socket:
            continue
        foundPair = s
        break
    pairs.append(Pair(socket, foundPair))