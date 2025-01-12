import asyncio
import websockets
import base64
import sounddevice as sd
import numpy as np
import json


async def receive_data():
    """Connect to the WebSocket server and display received messages."""
    uri = "ws://localhost:8765"  # WebSocket server URI
    print(f"Connecting to server at {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server! Waiting for messages...\n")
            
            while True:
                try:
                    # Receive a message from the server
                    message = await websocket.recv()
                    
                    # Attempt to parse the message as JSON
                    parsed_message = json.loads(message)
                    
                    if parsed_message["type"] == "text":
                        # Handle text messages
                        print(f"Text Message: {parsed_message['text1']} | {parsed_message['text2']}")
                    
                    elif parsed_message["type"] == "audio":
                        # Handle audio messages (base64-encoded)
                        encoded_audio = parsed_message['data']
                        audio_data = base64.b64decode(encoded_audio)
                        np_audio = np.frombuffer(audio_data, dtype=np.int16)
                        sd.play(np_audio, samplerate=22050)
                        sd.wait()

                except json.JSONDecodeError:
                    # Handle raw base64-encoded audio messages
                    print("Received raw base64 audio data.")
                    audio_data = base64.b64decode(message)
                    np_audio = np.frombuffer(audio_data, dtype=np.int16)
                    sd.play(np_audio, samplerate=22050)
                    sd.wait()

                except websockets.ConnectionClosed:
                    print("Connection closed by the server.")
                    break

                except Exception as e:
                    print(f"An error occurred: {e}")
                    break

    except ConnectionRefusedError:
        print(f"Unable to connect to server at {uri}. Is it running?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        print("Receiver client starting...")
        asyncio.run(receive_data())
    except Exception as e:
        print(f"An error occurred: {e}")