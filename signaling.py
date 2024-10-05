from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict
from collections import defaultdict

app = FastAPI()

# Stores active WebSocket connections mapped by session ID
active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

class ConnectionManager:
    def __init__(self):
        self.active_connections = defaultdict(list)

    async def connect(self, websocket: WebSocket, session_id: str):
        """Add a new WebSocket connection to the session."""
        await websocket.accept()
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove WebSocket connection from session."""
        self.active_connections[session_id].remove(websocket)
        if len(self.active_connections[session_id]) == 0:
            del self.active_connections[session_id]

    async def broadcast(self, message: str, session_id: str, sender: WebSocket):
        """Broadcast messages (SDP, ICE) within the session to all except the sender."""
        for connection in self.active_connections[session_id]:
            if connection != sender:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    # When a client connects, add it to the session group
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Receive messages (SDP or ICE candidate) from the WebSocket
            data = await websocket.receive_text()
            # Broadcast the message to all other participants in the same session
            await manager.broadcast(data, session_id, websocket)
    except WebSocketDisconnect:
        # Handle the disconnection and remove the client from the session
        manager.disconnect(websocket, session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
