import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import sys
from crc import encode_message, decode_message, introduce_error

HOST = socket.gethostbyname(socket.gethostname())
PORT = 1234

clients = []  # list of client sockets
names = {}    # map socket -> name
server_socket = None
server_running = False
accept_thread = None
lock = threading.Lock()  # ensures threads don’t modify clients/names at the same time.


def start_server(port=1234):
    global server_socket, server_running, accept_thread
    if server_running:
        gui_log('Server already running')
        return
    
    #Creating the main listening socket that clients will connect to
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #Allows the OS to reuse the port immediately after the server closes..
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, port))
        server_socket.listen()
    except Exception as e:
        gui_log(f'Failed to start server: {e}')
        return
    
    server_running = True
    gui_log(f'Server started successfully! Server running on {HOST}:{port}')
    gui_log(f'IP Address: {HOST}')
    gui_log(f'Port: {port}')
    gui_log('Waiting for connections...\n')

    #Starts a daemon thread to accept clients continuously in the background.
    accept_thread = threading.Thread(target=accept_clients, daemon=True)
    accept_thread.start()


def stop_server():
    global server_running, server_socket
    if not server_running:
        gui_log('Server not running')
        return
    gui_log('[SERVER SHUTDOWN]')
    broadcast_notice('Server is shutting down. See you again soon!')
    with lock:
        for c in clients[:]:
            try:
                c.close()
            except:
                pass
        clients.clear()
        names.clear()
    try:
        server_socket.close()
    except:
        pass
    server_socket = None
    server_running = False


#This function sends a string message over a TCP socket safely.
def safe_send(conn, text):
    try:
        conn.send(text.encode())
    except Exception:
        raise


#This function sends a message to all connected clients, except optionally the sender.
def broadcast_raw(encoded_text, sender_socket=None):
    with lock:
        for client in clients[:]:
            if client != sender_socket:
                try:
                    safe_send(client, encoded_text)

                except Exception:
                    try:
                        client.close()
                    except:
                        pass
                    try:
                        clients.remove(client)
                        if client in names:
                            del names[client]
                    except ValueError:
                        pass



def broadcast_notice(notice_text):
    encoded = encode_message(notice_text)
    broadcast_raw(encoded)


def broadcast_with_retry(message, sender_socket=None):
    encoded = encode_message(message)

    #Simulates a 10% chance of corruption.
    trial = introduce_error(encoded, error_prob=0.1)

    #Checks if the trial message would be considered valid.
    _, ok = decode_message(trial)
    if ok: #valid send to all clients
        broadcast_raw(trial, sender_socket)
    else: #invalid/corrupted send error message and retransmit original message
        notice = "[CRC ERROR]: Error in broadcast. Rebroadcasting..."
        gui_log(notice) 
        notice_encoded = encode_message(notice)
        broadcast_raw(notice_encoded)
        broadcast_raw(encoded, sender_socket)


def accept_clients():
    global server_running
    while server_running:
        try:
            client, addr = server_socket.accept()
        except Exception:
            break
        with lock:
            clients.append(client)
        gui_log(f'[CONNECTED] {addr}')
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()


#This function handles communication with a client.
def handle_client(client):
    try:
        raw = client.recv(4096).decode()
        name, ok = decode_message(raw)

        if not ok or name is None:
            try:
                client.send(encode_message("Invalid name CRC. Disconnecting.").encode())
            except:
                pass
            try:
                client.close()
            except:
                pass
            with lock:
                if client in clients:
                    clients.remove(client)
            return

        #Add the client to the names dictionary
        with lock:
            names[client] = name
        #Log the new connection in the GUI and broadcast to all clients
        gui_log(f'[NEW CONNECTION] Client {name} connected.')
        broadcast_notice(f'Client {name} has joined the chat!')

        while True:
            incoming = client.recv(4096).decode()
            if not incoming:
                break

            #decode the incoming client message to check for crc validity
            msg, ok = decode_message(incoming)

            #CORRUPTED/INVALID:
            if not ok:
                #Display the CRC error in the server GUI.
                gui_log(f'[CRC ERROR]: Dropped corrupted message from {name}.')
                try:
                    #Display in the client GUI that their message was not delivered.
                    client.send(encode_message("[CRC ERROR]: Your message was corrupted and was not delivered.").encode())
                except:
                    pass
                #Does not broadcast this message.
                continue
            
            #To handle the [bye] exit message
            if msg == '[bye]':
                gui_log(f'[DISCONNECTED] {name}')
                broadcast_notice(f'Client {name} has left the chat.')
                break

            #NOT CORRUPTED/VALID: Logs the message in the server GUI in the format
            gui_log(f'{name} > {msg}')
            #Broadcasts it to all other clients using
            broadcast_raw(encode_message(f'{name}: {msg}'), sender_socket=client)

    except Exception as e:
        pass
    finally: #cleanup if connection crash or client disconnects
        try:
            with lock:
                if client in clients:
                    clients.remove(client)
                if client in names:
                    del names[client]
        except:
            pass
        try:
            client.close()
        except:
            pass


# tkinter gui
root = tk.Tk()
root.title('Server Chat')

txt = scrolledtext.ScrolledText(root, state='disabled', width=60, height=20)
txt.grid(row=0, column=0, columnspan=4, padx=8, pady=8)

def gui_log(message):
    txt.configure(state='normal')
    txt.insert(tk.END, message + '\n')
    txt.see(tk.END)
    txt.configure(state='disabled')

entry_msg = tk.Entry(root, width=50)
entry_msg.grid(row=1, column=0, padx=8, pady=4)

def send_server_message():
    msg = entry_msg.get().strip()
    if not msg:
        return
    # o handle the [bye] as a shutdown request
    if msg == '[bye]':
        gui_log('[SERVER SHUTDOWN] (requested)')
        stop_server()
        entry_msg.delete(0, tk.END)
        return
    
    gui_log(f'Server > {msg}')
    # Messages typed from the server uses broadcast_with_retry to simulate possible corruption:
    # The initial broadcast is simulated (10% chance error). If corrupted, send error message and rebroadcast.
    broadcast_with_retry(f'Server: {msg}')
    entry_msg.delete(0, tk.END)

btn_send = tk.Button(root, text='Send', width=10, command=send_server_message)
btn_send.grid(row=1, column=1, padx=4)
btn_stop = tk.Button(root, text='Stop Server', width=12, command=stop_server)
btn_stop.grid(row=1, column=2, padx=4)
btn_start = tk.Button(root, text='Start Server', width=12, command=lambda: start_server(PORT))
btn_start.grid(row=1, column=3, padx=4)

def on_closing():
    stop_server()
    root.destroy()

root.protocol('WM_DELETE_WINDOW', on_closing)

if __name__ == '__main__':
    start_server(PORT)
    root.mainloop()
