# client.py
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from crc import encode_message, decode_message, introduce_error

PORT = 1234
client_socket = None
receive_thread = None
connected = False

def gui_log(message):
    def append():
        txt.configure(state='normal')
        txt.insert(tk.END, message + '\n')
        txt.see(tk.END)
        txt.configure(state='disabled')
    try:
        root.after(0, append)
    except Exception:
        append()

def connect_to_server():
    global client_socket, receive_thread, connected
    if connected:
        gui_log('Already connected')
        return
    server_ip = entry_ip.get().strip()
    port_text = entry_port.get().strip()
    name = entry_name.get().strip()
    if not server_ip or not name:
        gui_log('Server IP and Name required')
        return
    try:
        port = int(port_text) if port_text else PORT
    except ValueError:
        gui_log('Port must be a number')
        return
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, port))
    except Exception as e:
        gui_log(f'Connection failed: {e}')
        client_socket = None
        return

    name_msg = encode_message(name)
    try:
        client_socket.send(name_msg.encode())
    except Exception as e:
        gui_log(f'Failed to send name: {e}')
        client_socket.close()
        client_socket = None
        return

    connected = True
    gui_log(f'Connected to {server_ip}:{port} as {name}')
    set_connected_state(True)
    receive_thread = threading.Thread(target=receive_messages, daemon=True)
    receive_thread.start()

def disconnect_from_server():
    global client_socket, connected
    if not connected or client_socket is None:
        gui_log('Not connected')
        return
    try:
        bye_msg = encode_message('[bye]')
        bye_msg = introduce_error(bye_msg, error_prob=0.1)
        client_socket.send(bye_msg.encode())
    except:
        pass
    try:
        client_socket.close()
    except:
        pass
    client_socket = None
    connected = False
    gui_log('Disconnected')
    set_connected_state(False)

def receive_messages():
    global client_socket, connected
    while connected and client_socket:
        try:
            msg = client_socket.recv(4096).decode()
            if not msg:
                gui_log('Disconnected from server.')
                break
            
            text, ok = decode_message(msg)
            if not ok:
                gui_log('⚠️ Error detected in incoming message from server!')
                continue

            if text.lower().startswith('server is shutting down'):
                gui_log('Server is shutting down...')
                try:
                    root.after(0, root.destroy)
                except Exception:
                    pass
                break
            gui_log(text)
        except Exception:
            break
    try:
        if client_socket:
            client_socket.close()
    except:
        pass
    client_socket = None
    connected = False
    set_connected_state(False)

def send_message():
    global client_socket, connected
    if not connected or client_socket is None:
        gui_log('Not connected')
        return
    msg = entry_msg.get().strip()
    if not msg:
        return

    msg_crc = encode_message(msg)
    msg_crc = introduce_error(msg_crc, error_prob=0.1)

    try:
        client_socket.send(msg_crc.encode())
    except Exception as e:
        gui_log(f'Failed to send: {e}')
        entry_msg.delete(0, tk.END)
        return
    
    gui_log(f'You: {msg}')

    if msg == '[bye]':
        try:
            client_socket.close()
        except:
            pass
        connected = False
        set_connected_state(False)

    entry_msg.delete(0, tk.END)

# tkinter gui
root = tk.Tk()
root.title('Chat Client')

frame_top = tk.Frame(root)
frame_top.grid(row=0, column=0, padx=8, pady=8)

tk.Label(frame_top, text='Server IP:').grid(row=0, column=0)
entry_ip = tk.Entry(frame_top, width=15)
entry_ip.grid(row=0, column=1)

tk.Label(frame_top, text='Port:').grid(row=0, column=2)
entry_port = tk.Entry(frame_top, width=6)
entry_port.grid(row=0, column=3)
entry_port.insert(0, str(PORT))

tk.Label(frame_top, text='Your Name:').grid(row=0, column=4)
entry_name = tk.Entry(frame_top, width=15)
entry_name.grid(row=0, column=5)

btn_connect = tk.Button(frame_top, text='Connect', width=10, command=connect_to_server)
btn_connect.grid(row=0, column=6, padx=6)

btn_disconnect = tk.Button(frame_top, text='Disconnect', width=10, command=disconnect_from_server)
btn_disconnect.grid(row=0, column=7)

txt = scrolledtext.ScrolledText(root, state='disabled', width=60, height=20)
txt.grid(row=1, column=0, padx=8, pady=4)

frame_bottom = tk.Frame(root)
frame_bottom.grid(row=2, column=0, padx=8, pady=4)

entry_msg = tk.Entry(frame_bottom, width=50)
entry_msg.grid(row=0, column=0)

btn_send = tk.Button(frame_bottom, text='Send', width=10, command=send_message)
btn_send.grid(row=0, column=1, padx=6)

def set_connected_state(is_connected):
    # button and field state changes must run in main thread
    def apply():
        if is_connected:
            btn_connect.config(state='disabled')
            btn_disconnect.config(state='normal')
            btn_send.config(state='normal')
            entry_ip.config(state='disabled')
            entry_port.config(state='disabled')
            entry_name.config(state='disabled')
        else:
            btn_connect.config(state='normal')
            btn_disconnect.config(state='disabled')
            btn_send.config(state='disabled')
            entry_ip.config(state='normal')
            entry_port.config(state='normal')
            # keep name disabled after first use per requirement
            try:
                entry_name.config(state='disabled')
            except Exception:
                pass
    try:
        root.after(0, apply)
    except Exception:
        apply()

def on_closing():
    disconnect_from_server()
    root.destroy()

root.protocol('WM_DELETE_WINDOW', on_closing)

if __name__ == '__main__':
    # initial button states
    btn_disconnect.config(state='disabled')
    btn_send.config(state='disabled')
    root.mainloop()
