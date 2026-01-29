import socket
import tkinter as tk
from tkinter import messagebox
import threading
import json

SERVER_IP = '127.0.0.1'
PORT = 65432

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("DAT VE PHIM")
        self.buttons = {}
        
        # Giao diện lưới ghế
        frame = tk.Frame(root)
        frame.pack(pady=20)
        
        for i in range(1, 21):
            s_id = str(i)
            btn = tk.Button(frame, text=s_id, width=5, height=2, bg="green", fg="white",
                            command=lambda s=s_id: self.send_book(s))
            btn.grid(row=(i-1)//5, column=(i-1)%5, padx=2, pady=2)
            self.buttons[s_id] = btn

        self.connect()

    def connect(self):
        try:
            self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sk.connect((SERVER_IP, PORT))
            threading.Thread(target=self.listen, daemon=True).start()
        except: messagebox.showerror("Loi", "Khong ket noi duoc Server")

    def send_book(self, s_id):
        self.sk.sendall(json.dumps({"type": "book", "seat_id": s_id}).encode('utf-8'))

    def listen(self):
        while True:
            try:
                data = self.sk.recv(1024).decode('utf-8')
                msg = json.loads(data)
                if msg['type'] == 'init':
                    for s_id, status in msg['data'].items():
                        self.update_color(s_id, status)
                elif msg['type'] == 'update':
                    self.update_color(msg['seat_id'], msg['status'])
            except: break

    def update_color(self, s_id, status):
        # Quan trọng: Dùng after để cập nhật UI từ Thread
        self.root.after(0, self._change, s_id, status)

    def _change(self, s_id, status):
        if s_id in self.buttons:
            c = "red" if status == 1 else "green"
            st = "disabled" if status == 1 else "normal"
            self.buttons[s_id].config(bg=c, state=st)

root = tk.Tk()
App(root)
root.mainloop()