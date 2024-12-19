import asyncio
import websockets
import json

async def bridge_data():
    """
    Connect to the Fontys server to receive data and forward it to the Hume server.
    """
    fontys_server_uri = "ws://localhost:9000"  # Replace with the URI of the Fontys server
    hume_server_uri = "ws://localhost:8765"  # Replace with the URI of the Hume server

    while True:
        try:
            print(f"Connecting to Fontys server at {fontys_server_uri}...")
            async with websockets.connect(fontys_server_uri) as fontys_socket:
                print(f"Connected to Fontys server!")

                print(f"Connecting to Hume server at {hume_server_uri}...")
                async with websockets.connect(hume_server_uri) as hume_socket:
                    print(f"Connected to Hume server! Waiting for data...\n")

                    while True:
                        try:
                            # Receive data from Fontys server
                            message = await fontys_socket.recv()
                            print(f"Received data from Fontys server")

                            # Determine if the message is binary or text
                            if isinstance(message, (bytes, bytearray)):
                                print("Binary audio data detected. Forwarding to Hume server.")
                                await hume_socket.send(message)  # Forward binary data
                            else:
                                try:
                                    # Try parsing message as JSON for structured data forwarding
                                    parsed_message = json.loads(message)
                                    print(f"Parsed message: {parsed_message}")
                                    # Forward the parsed JSON to Hume server
                                    await hume_socket.send(json.dumps(parsed_message))
                                    print("Forwarded structured data to Hume server.")
                                except json.JSONDecodeError:
                                    # Forward raw text data as-is
                                    print("Unstructured text data detected. Forwarding as-is.")
                                    await hume_socket.send(message)

                        except websockets.exceptions.ConnectionClosed as e:
                            print(f"Connection to one of the servers closed: {e}")
                            break
                        except Exception as e:
                            print(f"An error occurred during data forwarding: {e}")

        except (ConnectionRefusedError, websockets.exceptions.InvalidURI) as e:
            print(f"Connection failed: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        print("Reconnecting to both servers in 5 seconds...\n")
        await asyncio.sleep(5)

if __name__ == "__main__":
    print("Starting Intermediate Client...")
    asyncio.run(bridge_data())
