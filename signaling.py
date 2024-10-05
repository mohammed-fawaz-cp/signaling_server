from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()
connected_clients = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    connected_clients[room_id] = connected_clients.get(room_id, [])
    connected_clients[room_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages, forwarding them to other clients...
            for client in connected_clients[room_id]:
                if client != websocket:
                    await client.send_text(data)
    except WebSocketDisconnect:
        connected_clients[room_id].remove(websocket)
        if not connected_clients[room_id]:  # Clean up empty room
            del connected_clients[room_id]

@app.get("/devices")
async def get_connected_devices():
    return {"devices": list(connected_clients.keys())}  # Return available room IDs
