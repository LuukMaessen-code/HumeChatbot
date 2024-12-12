import asyncio
import base64
import datetime
import os
import json
from dotenv import load_dotenv
from hume.client import AsyncHumeClient
from hume.empathic_voice.chat.socket_client import ChatConnectOptions, ChatWebsocketConnection
from hume.empathic_voice.chat.types import SubscribeEvent
from hume.empathic_voice.types import UserInput
from hume.core.api_error import ApiError
from hume import MicrophoneInterface, Stream
import websockets

clients = {}

class WebSocketHandler:
    """Handler for containing the EVI WebSocket and associated socket handling behavior."""

    def __init__(self, server_clients):
        """Construct the WebSocketHandler, initially assigning the socket to None and the byte stream to a new Stream object."""
        self.socket = None
        self.byte_strs = Stream.new()
        self.server_clients = server_clients  # Reference to the WebSocket server's clients

    async def register_client(self, websocket):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        # Receive client ID upon connection
        client_id = "HumeClient"
        clients[client_id] = websocket  # Register the client

    def set_socket(self, socket: ChatWebsocketConnection):
        """Set the socket."""
        self.socket = socket

    async def on_open(self):
        """Logic invoked when the WebSocket connection is opened."""
        print("WebSocket connection opened.")

    async def on_message(self, message: SubscribeEvent):
        """Callback function to handle a WebSocket message event."""
        scores = {}

        if message.type == "chat_metadata":
            message_type = message.type.upper()
            chat_id = message.chat_id
            chat_group_id = message.chat_group_id
            text = f"<{message_type}> Chat ID: {chat_id}, Chat Group ID: {chat_group_id}"
        elif message.type in ["user_message", "assistant_message"]:
            role = message.message.role.upper()
            message_text = message.message.content
            text = f"{role}: {message_text}"
            if message.from_text is False:
                scores = dict(message.models.prosody.scores)
            
            if message.type == "assistant_message":
                # Extract the top 3 emotions
                top_3_emotions = self._extract_top_n_emotions(scores, 3)
                # Send data to connected WebSocket server clients
                await self.broadcast_to_clients(message_text, top_3_emotions)
        elif message.type == "audio_output":
            message_str: str = message.data
            await self.broadcast_audio_to_clients(message_str)
            return
        elif message.type == "error":
            error_message: str = message.message
            error_code: str = message.code
            raise ApiError(f"Error ({error_code}): {error_message}")
        else:
            message_type = message.type.upper()
            text = f"<{message_type}>"
        
        # Print the formatted message
        self._print_prompt(text)

        # Extract and print the top 3 emotions inferred from user and assistant expressions
        if len(scores) > 0:
            top_3_emotions = self._extract_top_n_emotions(scores, 3)
            self._print_emotion_scores(top_3_emotions)
            print("")
        else:
            print("")
        
    async def on_close(self):
        """Logic invoked when the WebSocket connection is closed."""
        print("WebSocket connection closed.")

    async def on_error(self, error):
        """Logic invoked when an error occurs in the WebSocket connection."""
        print(f"Error: {error}")

    def _print_prompt(self, text: str) -> None:
        """Print a formatted message with a timestamp."""
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        now_str = now.strftime("%H:%M:%S")
        print(f"[{now_str}] {text}")

    def _extract_top_n_emotions(self, emotion_scores: dict, n: int) -> dict:
        """Extract the top N emotions based on confidence scores."""
        sorted_emotions = sorted(emotion_scores.items(), key=lambda item: item[1], reverse=True)
        return {emotion: score for emotion, score in sorted_emotions[:n]}

    def _print_emotion_scores(self, emotion_scores: dict) -> None:
        """Print the emotions and their scores in a formatted, single-line manner."""
        formatted_emotions = ' | '.join([f"{emotion} ({score:.2f})" for emotion, score in emotion_scores.items()])
        print(f"|{formatted_emotions}|")

    async def broadcast_to_clients(self, message_text, top_3_emotions):
        """Send the assistant message and top 3 emotions to all connected WebSocket server clients."""
        if self.server_clients:
            data = {
                "message": message_text,
                "top_emotions": top_3_emotions
            }
            message = json.dumps(data)
            await asyncio.gather(*[client.send(message) for client in self.server_clients if client.open])

    async def broadcast_audio_to_clients(self, audio_str):
        """Send the assistant message and top 3 emotions to all connected WebSocket server clients."""
        if self.server_clients:
            await asyncio.gather(*[client.send(audio_str) for client in self.server_clients if client.open])

async def websocket_server(server_clients):
    """WebSocket server to broadcast data to connected clients."""
    async def handler(websocket):
        server_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            server_clients.remove(websocket)

    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # Run forever


async def main() -> None:
    # Retrieve any environment variables stored in the .env file
    load_dotenv()

    # Retrieve the API key, Secret key, and EVI config id from the environment variables
    HUME_API_KEY = os.getenv("HUME_API_KEY")
    HUME_SECRET_KEY = os.getenv("HUME_SECRET_KEY")
    HUME_CONFIG_ID = os.getenv("HUME_CONFIG_ID")

    # Initialize the asynchronous client, authenticating with your API key
    client = AsyncHumeClient(api_key=HUME_API_KEY)

    # Define options for the WebSocket connection
    options = ChatConnectOptions(config_id=HUME_CONFIG_ID, secret_key=HUME_SECRET_KEY)

    # Set of connected WebSocket clients
    server_clients = set()

    # Start the WebSocket server
    server_task = asyncio.create_task(websocket_server(server_clients))

    # Instantiate the WebSocketHandler
    websocket_handler = WebSocketHandler(server_clients)

    # Open the WebSocket connection with the configuration options
    async with client.empathic_voice.chat.connect_with_callbacks(
        options=options,
        on_open=websocket_handler.on_open,
        on_message=websocket_handler.on_message,
        on_close=websocket_handler.on_close,
        on_error=websocket_handler.on_error
    ) as socket:

        # Set the socket instance in the handler
        websocket_handler.set_socket(socket)

        # Create asynchronous tasks
        microphone_task = asyncio.create_task(
            MicrophoneInterface.start(
                socket,
                allow_user_interrupt=False,
                byte_stream=websocket_handler.byte_strs
            )
        )

        # Schedule the coroutines to occur simultaneously
        await asyncio.gather(server_task, microphone_task)

# Execute the main asynchronous function using asyncio's event loop
if __name__ == "__main__":
    print("humeserver")
    asyncio.run(main())
