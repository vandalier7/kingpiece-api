
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

app = FastAPI()

connections = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    
    try:
        while True:
            data = await ws.receive_text()
            for socket in connections:
                await broadcast(socket, data)
    except WebSocketDisconnect:
        connections.remove(ws)

async def broadcast(socket: WebSocket, data: str):
    await socket.send_text(f"{data}")