import asyncio
import base64
import datetime
import json
import os
from dotenv import load_dotenv
from hume.client import AsyncHumeClient
from hume.empathic_voice.chat.socket_client import ChatConnectOptions, ChatWebsocketConnection
from hume.empathic_voice.chat.types import SubscribeEvent
from hume.core.api_error import ApiError
from hume import MicrophoneInterface, Stream
import websockets
from websockets.exceptions import ConnectionClosed


class WebSocketHandler:
    """Handler for managing Hume EVI WebSocket behavior and sending messages."""

    def __init__(self):
        self.socket = None
        self.byte_strs = Stream.new()

    def set_socket(self, socket: ChatWebsocketConnection):
        """Set the Hume WebSocket connection."""
        self.socket = socket

    async def handle_hume_message(self, message: SubscribeEvent):
        """Process and handle incoming Hume messages."""
        if message.type in ["user_message", "assistant_message"]:
            role = message.message.role.upper()
            content = message.message.content
            print(f"{role}: {content}")

            # Process message for broadcasting or further use
            scores = dict(message.models.prosody.scores) if not message.from_text else {}
            processed_message = {
                "content": content,
                "scores": scores,
            }

            return processed_message

        elif message.type == "error":
            error_message: str = message.message
            error_code: str = message.code
            raise ApiError(f"Error ({error_code}): {error_message}")

        return None

async def send_to_separate_server(message: str):
    """Send a message to a separate WebSocket server."""
    uri = "ws://localhost:8765"  # Replace with your separate WebSocket server's URI
    try:
        async with websockets.connect(uri) as websocket:
            # Send the message to the separate server
            await websocket.send(message)
            print(f"Sent to separate WebSocket server: {message}")
    except ConnectionRefusedError:
        print("Could not connect to the WebSocket server. Is it running?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

async def sending_handler(socket: ChatWebsocketConnection):
    """Handle sending messages over the Hume WebSocket and a separate WebSocket server.

    This method waits for user input and sends a UserInput or AssistantMessage message
    based on the provided input. The assistant's message is forwarded to a separate WebSocket server.
    """
    while True:
        # Wait for user input to determine message type and content
        message_type = input("Enter message type ('user' or 'assistant'): ").strip().lower()
        message_content = input("Enter the message content: ").strip()

        if message_type == "user":
            # Send a UserInput message to the Hume WebSocket
            user_input_message = UserInput(text=message_content)
            await socket.send_user_input(user_input_message)
        elif message_type == "assistant":
            # Send an assistant message to the separate WebSocket server
            await send_to_separate_server(message_content)
        else:
            print("Invalid message type. Please enter 'user' or 'assistant'.")


async def main():
    # Load environment variables
    load_dotenv()
    HUME_API_KEY = os.getenv("HUME_API_KEY")
    HUME_SECRET_KEY = os.getenv("HUME_SECRET_KEY")
    HUME_CONFIG_ID = os.getenv("HUME_CONFIG_ID")

    # Initialize Hume client
    client = AsyncHumeClient(api_key=HUME_API_KEY)
    options = ChatConnectOptions(config_id=HUME_CONFIG_ID, secret_key=HUME_SECRET_KEY)

    # Create WebSocket handler
    websocket_handler = WebSocketHandler()

    # Connect to the external WebSocket server
    uri = "ws://localhost:8765"  # Update to match your server's address
    async with websockets.connect(uri) as websocket:
        print("Connected to the WebSocket server.")

        # Connect to the Hume EVI WebSocket
        async with client.empathic_voice.chat.connect_with_callbacks(
            options=options,
            on_open=lambda: print("Hume connection opened."),
            on_message=websocket_handler.handle_hume_message,
            on_close=lambda: print("Hume connection closed."),
            on_error=lambda e: print(f"Hume error: {e}"),
        ) as hume_socket:
            websocket_handler.set_socket(hume_socket)

            # Optionally handle microphone input
            microphone_task = asyncio.create_task(
                MicrophoneInterface.start(
                    hume_socket,
                    allow_user_interrupt=False,
                    byte_stream=websocket_handler.byte_strs,
                )
            )

            # Handle user input and forward to Hume or server
            while True:
                user_input = input("Enter a message to send: ")
                if user_input.lower() == "exit":
                    print("Exiting application.")
                    break

                # Send user input to Hume
                await hume_socket.send_user_input({"text": user_input})

                # Forward processed messages to the external server
                hume_message = await websocket_handler.handle_hume_message(SubscribeEvent(
                    type="user_message", 
                    message={"role": "user", "content": user_input}
                ))
                await websocket_handler.send_to_websocket_server(websocket, hume_message)

            # Cancel the microphone task if active
            if microphone_task:
                microphone_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
