import asyncio
import websockets
import base64
import sounddevice as sd
import numpy as np
import json

async def receive_data():
    """Connect to the WebSocket server and display received messages."""
    uri = "ws://localhost:9000"  
    # Send client ID
    client_id = "frontClient"
    print(f"Connecting to server at {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server! Waiting for messages...\n")

            # Send the client ID to the server after connecting
            await websocket.send(client_id)
            print(f"Client ID {client_id} sent to the server.")
            
            while True:
                try:
                    # Receive a message from the server
                    message = await websocket.recv()
                    
                    # Parse the message as JSON
                    parsed_message = json.loads(message)
                    
                    if parsed_message["type"] == "text":
                        # Handle text messages
                        print(f"Text Message: {parsed_message['data']}")
                    else:
                        # Handle audio messages
                        encoded_audio = message
                        audio_data = base64.b64decode(encoded_audio)
                        np_audio = np.frombuffer(audio_data, dtype=np.int16)
                        sd.play(np_audio, samplerate=44100)
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
        print("recieverclient:")
        asyncio.run(receive_data())
    except Exception as e:
        print(f"An error occurred: {e}")
