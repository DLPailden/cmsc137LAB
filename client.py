import socket
import threading

# Connect to server
server_ip = input("Enter the server IP address: ")
PORT = 1234
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((server_ip, PORT))

name = input("Enter your name: ")
client.send(name.encode())

# Receive messages from the server
def receive():
    while True:
        try:
            msg = client.recv(1024).decode()
            if not msg:
                print("Disconnected from server.")
                break
            print(msg)
        except:
            break
    client.close()


# Send messages to the server
def write():
    while True:
        msg = input()
        try:
            client.send(msg.encode())
            if msg == "[bye]":
                client.close()
                break
        except:
            print("Connection lost. Exiting chat.")
            break


# Run both receive and write threads
threading.Thread(target=receive).start()
threading.Thread(target=write).start()
