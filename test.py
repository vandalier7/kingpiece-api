
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

app = FastAPI()

class Pair:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    
    def broadcastEstablishment(self):
        broadcast(self.a, "{" + f'"type": "notif", "payload": "You are talking to {connections[self.b]}!"' + "}") 
        broadcast(self.b, "{" + f'"type": "notif", "payload": "You are talking to {connections[self.a]}!"' + "}") 
    


connections = {}
pairs = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections[ws] = "user" + str(len(connections))
    
    await onConnect(ws)
    try:
        while True:
            data = await ws.receive_text()
            for socket in connections:
                await broadcast(socket, data)
    except WebSocketDisconnect:
        connections.pop(ws)

async def broadcast(socket: WebSocket, data: str):
    await socket.send_text(f"{data}")

async def onConnect(socket: WebSocket):
    try:
        await broadcast(socket, '{"type": "notif", "payload": "Connected to server!"}')
    except WebSocketDisconnect:
        connections.pop(socket)
    if len(connections) < 2:
        return
    foundPair = None
    for s in connections:
        if s == socket:
            continue
        foundPair = s
        break
    pairs.append(Pair(socket, foundPair))
