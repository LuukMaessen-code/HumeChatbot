import asyncio
import websockets
import base64
import sounddevice as sd
import numpy as np
import json
import threading

FONTYS_SERVER_URI = "ws://localhost:8765"  # URI of the Fontys server
SAMPLERATE = 44100  # Sampling rate for audio

async def send_audio_to_server(audio_queue):
    """
    Sends audio data from the microphone to the Fontys server.
    """
    try:
        print(f"Connecting to Fontys server at {FONTYS_SERVER_URI}...")
        async with websockets.connect(FONTYS_SERVER_URI) as fontys_socket:
            print("Connected to Fontys server. Streaming microphone audio...")

            while True:
                # Wait for audio data from the queue
                audio_data = await audio_queue.get()
                
                # Encode audio data as base64
                encoded_audio = base64.b64encode(audio_data).decode("utf-8")
                message = json.dumps({"type": "audio", "data": encoded_audio})
                
                # Send audio data to the Fontys server
                await fontys_socket.send(message)
                print("Audio data sent to Fontys server.")

    except websockets.ConnectionClosed:
        print("Connection closed by Fontys server.")
    except Exception as e:
        print(f"An error occurred while sending audio: {e}")

def capture_microphone(audio_queue):
    """
    Captures microphone input and places the audio data into an asyncio queue.
    """
    def audio_callback(indata, frames, time, status):
        # Callback for capturing audio data
        if status:
            print(f"Audio input error: {status}")
        audio_queue.put_nowait(indata.tobytes())  # Convert numpy array to bytes and add to the queue

    # Open a stream for microphone input
    with sd.InputStream(samplerate=SAMPLERATE, channels=1, callback=audio_callback, dtype=np.int16):
        print("Microphone capture started. Press Ctrl+C to stop.")
        asyncio.get_event_loop().run_forever()  # Keep the stream open

async def receive_data(audio_queue):
    """
    Connect to the WebSocket server and display/play received messages.
    """
    uri = FONTYS_SERVER_URI  # WebSocket server URI
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
                        sd.play(np_audio, samplerate=SAMPLERATE)
                        sd.wait()

                except json.JSONDecodeError:
                    # Handle raw base64-encoded audio messages
                    print("Received raw base64 audio data.")
                    audio_data = base64.b64decode(message)
                    np_audio = np.frombuffer(audio_data, dtype=np.int16)
                    sd.play(np_audio, samplerate=SAMPLERATE)
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

async def main():
    # Create a queue to share audio data between the threads
    audio_queue = asyncio.Queue()

    # Start the microphone capturing thread
    threading.Thread(target=capture_microphone, args=(audio_queue,), daemon=True).start()

    # Start tasks to handle receiving and sending data
    await asyncio.gather(
        send_audio_to_server(audio_queue),  # Send microphone data to Fontys server
        receive_data(audio_queue)          # Receive and play data from the server
    )

if __name__ == "__main__":
    try:
        print("Receiver client starting...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nReceiver client stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")
