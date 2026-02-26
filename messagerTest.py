import asyncio
import websockets
import json

username = input("Enter your username: ")
print("Connecting, Please Wait")

class Message:
    def __init__(self, sender, message):
        self.sender = sender
        self.content = message
        self.type = "message"
    
    def to_json(self):
        return json.dumps({"sender": self.sender, "content": self.content, "type": self.type})
    
    @classmethod
    def from_json(cls, data: str):
        d = json.loads(data)
        return cls(d["sender"], d["content"])


async def receive(ws):
    while True:
        jsn = await ws.recv()
        parsed = json.loads(jsn)
        if parsed["type"] == "message":
            msg = Message.from_json(jsn)
            if msg.sender != username:
                print(msg.sender + ": " + msg.content)
        if parsed["type"] == "notif":
            print(parsed["payload"])

async def send(ws):
    while True:
        msg = await asyncio.get_event_loop().run_in_executor(None, input)
        msgObj = Message(username, msg)
        await ws.send(msgObj.to_json())

async def main():
    async with websockets.connect("wss://overflowing-dream-production.up.railway.app/ws", open_timeout=30) as ws:
        print("Connected!")
        await asyncio.gather(receive(ws), send(ws))

asyncio.run(main())