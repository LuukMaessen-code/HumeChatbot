import asyncio
import websockets

async def receive_data():
    """Connect to the WebSocket server and display received messages."""
    uri = "ws://localhost:9000"  # Replace with the URI of your second server
    print(f"Connecting to server at {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server! Waiting for messages...\n")
            
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
    except ConnectionRefusedError:
        print(f"Unable to connect to server at {uri}. Is it running?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(receive_data())
    except Exception as e:
        print(f"An error occurred: {e}")
