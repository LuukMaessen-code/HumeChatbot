import asyncio
import websockets

async def sender():
    uri = "ws://localhost:8765"  # Replace with the server address
    try:
        async with websockets.connect(uri) as websocket:
            message = input("Enter a message to send: ")
            await websocket.send(message)
            print(f"Message sent: {message}")
    except ConnectionRefusedError:
        print("Could not connect to the WebSocket server. Is it running?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(sender())