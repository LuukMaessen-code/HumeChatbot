import asyncio
import websockets
import json

async def bridge_data():
    """
    Connect to the first WebSocket server to receive data and forward it to the second WebSocket server.
    """
    first_server_uri = "ws://localhost:8765"  # Replace with the URI of the first server
    second_server_uri = "ws://localhost:9000"  # Replace with the URI of the second server

    while True:
        try:
            print(f"Connecting to first server at {first_server_uri}...")
            async with websockets.connect(first_server_uri) as first_server_socket:
                print(f"Connected to first server! Waiting for data...\n")
                
                print(f"Connecting to second server at {second_server_uri}...")
                async with websockets.connect(second_server_uri) as second_server_socket:
                    print(f"Connected to second server! Forwarding data...\n")

                    while True:
                        try:
                            # Receive data from the first server
                            message = await first_server_socket.recv()
                            print("Received data from first server:")
                            print(message)

                            # Forward the message to the second server
                            await second_server_socket.send(message)
                            print("Forwarded data to second server.\n")

                        except websockets.exceptions.ConnectionClosed as e:
                            print(f"Connection to one of the servers closed: {e}")
                            break
                        except Exception as e:
                            print(f"An error occurred: {e}")
                            break
        except (ConnectionRefusedError, websockets.exceptions.InvalidURI) as e:
            print(f"Connection failed: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        print("Reconnecting to both servers in 5 seconds...\n")
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(bridge_data())
