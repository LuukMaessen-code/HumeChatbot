import asyncio
import websockets
from websockets.exceptions import ConnectionClosed
import json

class WebSocketHandler:
    def __init__(self):
        self.clients = set()  # To track connected WebSocket clients

    async def register_client(self, websocket):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        print(f"Client registered: {websocket.remote_address}")

    async def on_message(self, websocket):
        """Handle messages from a client and broadcast to others."""
        try:
            async for message in websocket:
                print(f"Message received from {websocket.remote_address}")

                try:
                    # Attempt to parse the message as JSON
                    parsed_message = json.loads(message)
                    message_type = parsed_message.get("type")

                    if message_type == "text":
                        # Handle text message
                        text1 = parsed_message.get("text1", "")
                        text2 = parsed_message.get("text2", "")
                        print(f"Text Message: {text1} | {text2}")

                        # Broadcast text message to all clients except the sender
                        await self.broadcast_message(
                            websocket, {"type": "text", "text1": text1, "text2": text2}
                        )

                    elif message_type == "audio":
                        # Handle audio message
                        audio_data = parsed_message.get("data", "")
                        print(f"Audio data received")

                        # Broadcast audio data to all clients except the sender
                        await self.broadcast_message(
                            websocket, {"type": "audio", "data": audio_data}
                        )

                except json.JSONDecodeError:
                    # Handle raw base64-encoded audio data
                    print("Received base64-encoded audio data")
                    if isinstance(message, str):
                        # Broadcast base64 audio data to all clients except the sender
                        await self.broadcast_message(websocket, message)

        except ConnectionClosed:
            print(f"Connection closed: {websocket.remote_address}")
        # Do not unregister the client here

    async def broadcast_message(self, sender, message):
        """Broadcast a message to all clients except the sender."""
        for client in self.clients:
            if client != sender:
                try:
                    if isinstance(message, dict):
                        await client.send(json.dumps(message))
                    else:
                        await client.send(message)
                except Exception as e:
                    print(f"Error sending message to {client.remote_address}: {e}")

    async def websocket_server(self, host="localhost", port=9000):
        """WebSocket server to handle clients."""
        async def handler_logic(websocket):
            print(f"Client connected: {websocket.remote_address}")
            await self.register_client(websocket)
            await self.on_message(websocket)

        server = await websockets.serve(handler_logic, host, port)
        print(f"WebSocket server listening on ws://{host}:{port}")
        return server


async def main():
    websocket_handler = WebSocketHandler()
    await websocket_handler.websocket_server()
    await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        print("Starting WebSocket server...")
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")
