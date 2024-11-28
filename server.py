import asyncio
import websockets
import websockets
from websockets.exceptions import ConnectionClosed


class WebSocketHandler:
    
    def __init__(self):
        self.socket = None
        self.clients = set()  # To track connected WebSocket clients
        
    
            
    async def register_client(self, websocket):
        """Register a new WebSocket client."""
        self.clients.add(websocket)

    async def unregister_client(self, websocket):
        """Unregister a WebSocket client."""
        self.clients.discard(websocket)
            
    async def on_open(self):
        """Logic invoked when the WebSocket connection is opened."""
        print("WebSocket connection opened.")
            
    async def on_close(self):
        """Logic invoked when the WebSocket connection is closed."""
        print("WebSocket connection closed.")

    async def on_error(self, error):
        """Handle WebSocket errors."""
        print(f"Error: {error}")
        
async def websocket_server(handler: WebSocketHandler, host="localhost", port=8765):
    """WebSocket server to handle clients."""
    async def handler_logic(websocket):
        print(f"Client connected: {websocket.remote_address}")
        await handler.register_client(websocket)
        try:
            async for message in websocket:
                print(f"Message received from {websocket.remote_address}: {message}")
                # Broadcast the message to all connected clients
                for client in handler.clients:
                    if client != websocket:  # Avoid echoing the message back to the sender
                        await client.send(f"Broadcast from {websocket.remote_address}: {message}")
        except websockets.ConnectionClosed:
            print(f"Client {websocket.remote_address} disconnected.")
        finally:
            await handler.unregister_client(websocket)
            print(f"Client {websocket.remote_address} removed from the set.")

    server = await websockets.serve(handler_logic, host, port)
    print(f"WebSocket server listening on ws://{host}:{port}")
    return server





async def main():
    # Create WebSocket handler
    websocket_handler = WebSocketHandler()

    # Start the local WebSocket server
    await websocket_server(websocket_handler)

    # Keep the server running
    await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")

