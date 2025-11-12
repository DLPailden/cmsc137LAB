import socket
import threading

# Server configuration
HOST = socket.gethostbyname(socket.gethostname())
PORT = 1234

# Create socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
print(f"[SERVER STARTED] Listening on address: {HOST} and port:{PORT}")

server.listen()
print("Waiting for clients... ")


clients = []  # List of connected client sockets
names = {}    # Map client sockets -> names

# Broadcast message to all clients
def broadcast(message, sender_socket=None):
    for client in clients:
        if client != sender_socket:  # don't send message back to sender
            try:
                client.send(message.encode())
            except:
                if client in clients:
                    clients.remove(client)

# Handle each connected client
def handle_client(client):
    name = client.recv(1024).decode()
    names[client] = name
    print(f"[NEW CONNECTION] {name} connected.")
    broadcast(f"{name} has joined the chat!")

    while True:
        try:
            msg = client.recv(1024).decode()
            if not msg:
                break

            if msg == "[bye]":
                print(f"[DISCONNECTED] {name}")
                broadcast(f"{name} has left the chat.")
                break

            print(f"{name} > {msg}")
            broadcast(f"{name}: {msg}", client)

        except:
            break

    # Cleanup after disconnect
    if client in clients:
        clients.remove(client)
    if client in names:
        del names[client]
    client.close()

# Accept new clients continuously
def receive_connections():
    while True:
        client, address = server.accept()
        clients.append(client)
        print(f"[CONNECTED] {address}")
        threading.Thread(target=handle_client, args=(client,)).start()

# Allow the server operator to send messages
def server_chat():
    while True:
        msg = input()
        if msg == "[bye]":
            print("[SERVER SHUTDOWN]")
            broadcast("Server is shutting down...")
            for c in clients:
                c.close()
            server.close()
            break
        else:
            print(f"Server > {msg}")
            broadcast(f"Server: {msg}")

# Run both threads
threading.Thread(target=receive_connections, daemon=True).start()
server_chat()
