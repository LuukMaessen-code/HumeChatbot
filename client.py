import asyncio
import websockets
import base64
import sounddevice as sd
import numpy as np
import json
import time


def fade_in(audio_data, duration, samplerate):
    """
    Apply a fade-in effect to the audio data. This is to remove an audio pop from happening upon playing the audio.
    Args:
        audio_data: NumPy array containing the audio samples.
        duration: Duration of the fade-in (in seconds).
        samplerate: Sample rate of the audio (e.g., 22050 Hz).
    Returns:
        NumPy array with fade-in applied.
    """
    fade_samples = int(duration * samplerate)
    fade_curve = np.linspace(0, 1, fade_samples, dtype=np.float32)  # Create fade curve
    faded_audio = audio_data.astype(np.float32)  # Convert to float for processing

    # Apply the fade-in curve
    faded_audio[:fade_samples] *= fade_curve

    # Convert back to int16 to match the original audio format
    return faded_audio.astype(np.int16)


async def connect_to_server(uri):
    """Attempt to connect to the WebSocket server and handle messages."""
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
                        print(f"Text Message: {parsed_message['text1']}")

                        # Parse the JSON string for emotions
                        emotions = json.loads(parsed_message['text2'])

                        # Display each emotion on a separate line
                        for emotion, score in emotions.items():
                            print(f"{emotion}: {score}")

                        # Add a blank line for spacing
                        print("")

                except json.JSONDecodeError:
                    # Handle raw base64-encoded audio messages
                    audio_data = base64.b64decode(message)
                    np_audio = np.frombuffer(audio_data, dtype=np.int16).copy()

                    # Apply fade-in effect (e.g., 50 ms duration)
                    np_audio = fade_in(np_audio, duration=0.05, samplerate=22050)

                    sd.play(np_audio, samplerate=22050)
                    sd.wait()

                    # Add type to differentiate playback audio
                    playback_message = json.dumps({"type": "playback_audio"})
                    await websocket.send(playback_message)  # Inform the backend it's playback audio

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


async def receive_data_with_retry():
    """Continuously attempt to connect to the server with a retry mechanism."""
    uri = "ws://localhost:8765"  # WebSocket server URI
    while True:
        await connect_to_server(uri)
        print("Retrying connection in 3 seconds...\n")
        await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        print("Receiver client starting...")
        asyncio.run(receive_data_with_retry())
    except Exception as e:
        print(f"An error occurred: {e}")
