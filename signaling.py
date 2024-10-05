from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store connected clients
connected_clients = {}

class Client(BaseModel):
    phone_number: str

@app.post("/register")
async def register_client(client: Client):
    if client.phone_number not in connected_clients:
        connected_clients[client.phone_number] = {"ws": None}
        return {"status": "success", "message": "Client registered"}
    return {"status": "error", "message": "Client already registered"}

@app.get("/clients")
async def get_clients():
    return {"clients": list(connected_clients.keys())}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    if client_id not in connected_clients:
        await websocket.close(code=1000)
        return

    connected_clients[client_id]["ws"] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message["type"] == "offer" or message["type"] == "answer" or message["type"] == "ice-candidate":
                target_client = message["target"]
                if target_client in connected_clients and connected_clients[target_client]["ws"]:
                    await connected_clients[target_client]["ws"].send_text(data)
    except WebSocketDisconnect:
        connected_clients[client_id]["ws"] = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)