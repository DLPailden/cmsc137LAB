import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import sys

# basic server GUI/chat using same protocol as original scripts
HOST = socket.gethostbyname(socket.gethostname())
PORT = 1234

clients = []  # list of client sockets
names = {}    # map socket -> name
server_socket = None
server_running = False
accept_thread = None


def start_server(port=1234):
    global server_socket, server_running, accept_thread
    if server_running:
        gui_log('Server already running')
        return
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    accept_thread = threading.Thread(target=accept_clients, daemon=True)
    accept_thread.start()


def stop_server():
    global server_running, server_socket
    if not server_running:
        gui_log('Server not running')
        return
    gui_log('[SERVER SHUTDOWN]')
    # first notify clients with the shutdown token so they close their GUIs
    broadcast('Server is shutting down. See you again soon!')
    # close all client sockets
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


def broadcast(message, sender_socket=None):
    for client in clients[:]:
        if client != sender_socket:
            try:
                client.send(message.encode())
            except Exception:
                try:
                    clients.remove(client)
                except ValueError:
                    pass


def accept_clients():
    global server_running
    while server_running:
        try:
            client, addr = server_socket.accept()
        except Exception:
            break
        clients.append(client)
        gui_log(f'[CONNECTED] {addr}')
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()


def handle_client(client):
    try:
        name = client.recv(1024).decode()
    except Exception:
        try:
            client.close()
        except:
            pass
        return
    names[client] = name
    gui_log(f'[NEW CONNECTION] Client {name} connected.')
    broadcast(f'Client {name} has joined the chat!')

    while True:
        try:
            msg = client.recv(1024).decode()
            if not msg:
                break
            if msg == '[bye]':
                gui_log(f'[DISCONNECTED] {name}')
                broadcast(f'Client {name} has left the chat.')
                break
            gui_log(f'{name} > {msg}')
            broadcast(f'{name}: {msg}', client)
        except Exception:
            break

    # cleanup
    try:
        if client in clients:
            clients.remove(client)
    except ValueError:
        pass
    if client in names:
        del names[client]
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
    # treat typing the special token '[bye]' as a shutdown request
    if msg == '[bye]':
        gui_log('[SERVER SHUTDOWN] (requested)')
        stop_server()
        entry_msg.delete(0, tk.END)
        return
    gui_log(f'Server > {msg}')
    broadcast(f'Server: {msg}')
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
    # start server automatically (optional). Keep original behavior similar: start immediately
    start_server(PORT)
    root.mainloop()
