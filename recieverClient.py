import asyncio
import websockets
import base64
import pyaudio

# PyAudio Configuration
FORMAT = pyaudio.paInt16  # Adjust based on your audio format
CHANNELS = 1              # Number of audio channels
RATE = 44100              # Sample rate (Hz)

async def receive_data():
    """Connect to the WebSocket server and display received messages."""
    uri = "ws://localhost:9000"  
    # Send client ID
    client_id = "frontClient"
    print(f"Connecting to server at {uri}...")
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        output=True
    )

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
                    print(f"Received message: {message}")
                except websockets.ConnectionClosed:
                    print("Connection closed by the server.")
                    break
                except Exception as e:
                    print(f"An error occurred: {e}")
                    break
                try:
                    # Recieve and play audio data
                    encoded_data = await websocket.recv()
                    audio_data = base64.b64decode(encoded_data)
                    if audio_data:
                        # Play audio data
                        stream.write(audio_data)
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
