import socket

#Set Socket
server = socket.socket()
host_name = socket.gethostname()		#device name
ip = socket.gethostbyname(host_name)		#IP address of device
port = 1234					#Port to listen at for connection
server.bind((ip, port))
print(f"Server has started on address: {ip} and port: {port}") 

#listen to incoming connections
server.listen()
print("Waiting for clients... ")

#get client information
(c_socket, c_address) = server.accept()
c_name = c_socket.recv(1024).decode()
print(f"{c_name} at '{c_address}' has joined the server")

#Welcome message
msg = f"Hi {c_name}! Welcome to the server. Type [bye] to exit the server"
c_socket.send(msg.encode())

#Communication Loop 
while True:
	#receive message
	recv_msg = c_socket.recv(1024).decode()
	print(f"{c_name} > {recv_msg}")
	
	if recv_msg == "[bye]":
		print(f"{c_name} has disconnected")
		c_socket.close()			#Close connection to client
		break
	
	#send message
	send_msg = input("Server > ")
	c_socket.send(send_msg.encode())
