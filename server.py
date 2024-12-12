import asyncio
import websockets
import websockets
from websockets.exceptions import ConnectionClosed
import json

# Dictionary to store connected clients
clients = {}

class WebSocketHandler:
    
    def __init__(self):
        self.socket = None
        self.clients = set()  # To track connected WebSocket clients
            
    async def register_client(self, websocket):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        # Receive client ID upon connection
        if (await websocket.recv()):
            client_id = await websocket.recv()
            clients[client_id] = websocket  # Register the client
            print(clients)
        else:
            client_id = "HumeClient"
            clients[client_id] = websocket
            print(clients)

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

    async def on_message(self, websocket, handler):
        try:
            async for message in websocket:
                print(f"Message received from {websocket.remote_address}: {message}")
                print(f"clients connected:{clients}")
                # If the message is a JSON with text data
                try:
                    parsed_message = json.loads(message)
                    message_type = parsed_message.get("type")

                    if message_type == "text":
                        # Handle text message containing two different text pieces
                        print(f"Text Message: {parsed_message['text1']} | {parsed_message['text2']}")
                        # You can broadcast or process the text data as needed

                    elif message_type == "audio":
                        # Handle audio message (base64-encoded)
                        print(f"Audio data received")
                        audio_data = parsed_message['data']
                        # Forward audio to "frontClient" or process
                        if "frontClient" in clients:
                            front_websocket = clients["frontClient"]
                            await front_websocket.send(json.dumps({"type": "audio", "data": audio_data}))
                            print(f"Audio data forwarded to frontClient")
                
                except json.JSONDecodeError:
                    # Handle raw base64-encoded audio data as a string
                    print("Received base64-encoded audio data")
                    if isinstance(message, str):
                        # Send base64 audio data to "frontClient"
                        if "frontClient" in clients:
                            front_websocket = clients["frontClient"]
                            await front_websocket.send(message)
                            print(f"Base64 audio forwarded to frontClient")
                
        except websockets.ConnectionClosed:
            print(f"Client {websocket.remote_address} disconnected.")
        finally:
            await handler.unregister_client(websocket)

    # async def on_message(self, websocket, handler):
    #     try:
    #         async for message in websocket:
    #             print(f"Message received from {websocket.remote_address}: {message}")
    #             # Broadcast the message to all connected clients
    #             for client in handler.clients:
    #                 if client != websocket:  # Avoid echoing the message back to the sender
    #                     await client.send(f"Broadcast from {websocket.remote_address}: {message}")
    #     except websockets.ConnectionClosed:
    #         print(f"Client {websocket.remote_address} disconnected.")
    #     finally:
    #         await handler.unregister_client(websocket)
    #         print(f"Client {websocket.remote_address} removed from the set.")

    # async def on_audio_recieve(self, websocket, clients):
    #     client_id = clients.client_id

    #     try:
    #         # Receive a message from the client
    #         message = await websocket.recv()

    #         # Handle audio data forwarding
    #         if client_id != "frontClient" and isinstance(message, str):
    #             print(f"Audio data received from {client_id}")
                
    #             # Forward the audio data to "frontClient"
    #             if "frontClient" in clients:
    #                 front_websocket = clients["frontClient"]
    #                 await front_websocket.send(message)
    #                 print(f"Audio data forwarded to frontClient")
    #             else:
    #                 print("frontClient is not connected.")
        
async def websocket_server(handler: WebSocketHandler, host="localhost", port=9000):
    """WebSocket server to handle clients."""
    async def handler_logic(websocket):
        print(f"Client connected: {websocket.remote_address}")
        await handler.register_client(websocket)
        await handler.on_message(websocket, handler)

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
        print("server")
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")

