import asyncio
import websockets
import json

username = input("Enter your username: ")

class Message:
    def __init__(self, sender, message):
        self.sender = sender
        self.content = message 
    
    def to_json(self):
        return json.dumps({"sender": self.sender, "content": self.content})
    
    @classmethod
    def from_json(cls, data: str):
        d = json.loads(data)
        return cls(d["sender"], d["content"])


async def receive(ws):
    while True:
        jsn = await ws.recv()
        msg = Message.from_json(jsn)
        if msg.sender != username:
            print(msg.sender + ": " + msg.content)

async def send(ws):
    while True:
        msg = await asyncio.get_event_loop().run_in_executor(None, input)
        msgObj = Message(username, msg)
        await ws.send(msgObj.to_json())

async def main():
    async with websockets.connect("ws://192.168.1.7:8000/ws") as ws:
        await asyncio.gather(receive(ws), send(ws))

asyncio.run(main())