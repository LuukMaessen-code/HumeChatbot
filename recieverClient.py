import asyncio
import websockets

async def receiver():
    uri = "ws://localhost:8765"  # Replace with the server address
    async with websockets.connect(uri) as websocket:
        print("Connected to the server. Waiting for a message...")
        while True:
            try:
                message = await websocket.recv()
                print(f"Message received: {message}")
            except websockets.ConnectionClosed:
                print("Connection closed by the server.")
                break

if __name__ == "__main__":
    asyncio.run(receiver())