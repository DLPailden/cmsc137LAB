import socket

#Set Socket
# create new socket object
client = socket.socket()
port = 1234

c_name = input("Enter your name: ")
ip = input("Enter the IP Address of the server: ")
client.connect((ip, port))
client.send(c_name.encode())

#Communication Loop 
while True:
	#receive message
	recv_msg = client.recv(1024).decode()
	print(f"Server > {recv_msg}")
	
	#send message
	send_msg = input("You > ")
	client.send(send_msg.encode())
	
	if send_msg == "[bye]":
		print("Disconnecting from server...")
		client.close()				#close connection with server
		print("Ending program...")
		break