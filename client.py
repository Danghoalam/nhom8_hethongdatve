import socket
import tkinter as tk
from tkinter import messagebox
import threading
import json

# Nếu chạy khác máy, hãy thay '127.0.0.1' bằng IP của máy Server
SERVER_IP = '127.0.0.1'
PORT = 65432

class CinemaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HỆ THỐNG ĐẶT VÉ NHÓM 8")
        self.root.geometry("400x500")
        
        # Tiêu đề & Thông báo User
        tk.Label(root, text="MÀN HÌNH CHIẾU PHIM", bg="black", fg="white", font=("Arial", 12, "bold")).pack(fill="x", pady=5)
        
        self.status_label = tk.Label(root, text="Đang kết nối đến server...", fg="blue", font=("Arial", 9, "italic"))
        self.status_label.pack(pady=5)

        # Khung chứa danh sách ghế
        self.seat_frame = tk.Frame(root)
        self.seat_frame.pack(pady=10)
        
        self.buttons = {}
        for i in range(1, 21):
            s_id = str(i)
            btn = tk.Button(self.seat_frame, text=f"Ghế {s_id}", width=8, height=2, 
                            bg="#2ecc71", fg="white", font=("Arial", 9, "bold"),
                            command=lambda s=s_id: self.send_booking(s))
            btn.grid(row=(i-1)//4, column=(i-1)%4, padx=5, pady=5)
            self.buttons[s_id] = btn

        self.connect_to_server()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((SERVER_IP, PORT))
            self.status_label.config(text="Kết nối thành công! Vui lòng chọn ghế.")
            threading.Thread(target=self.receive_data, daemon=True).start()
        except:
            messagebox.showerror("Lỗi", "Không thể kết nối đến Server!")
            self.root.destroy()

    def send_booking(self, seat_id):
        try:
            data = json.dumps({"type": "book", "seat_id": seat_id})
            self.client_socket.sendall(data.encode('utf-8'))
        except:
            messagebox.showerror("Lỗi", "Mất kết nối với Server.")

    def receive_data(self):
        while True:
            try:
                raw_data = self.client_socket.recv(1024).decode('utf-8')
                if not raw_data: break
                msg = json.loads(raw_data)
                
                if msg['type'] == 'init':
                    for s_id, status in msg['data'].items():
                        self.update_ui(s_id, status)
                elif msg['type'] == 'update':
                    self.update_ui(msg['seat_id'], msg['status'], msg.get('user'))
            except:
                break

    def update_ui(self, seat_id, status, user_info=None):
        # Đưa việc cập nhật giao diện vào luồng chính của Tkinter
        self.root.after(0, self._apply_ui_change, seat_id, status, user_info)

    def _apply_ui_change(self, seat_id, status, user_info):
        if seat_id in self.buttons:
            if status == 1:
                self.buttons[seat_id].config(bg="#e74c3c", state="disabled") # Màu đỏ
                if user_info:
                    self.status_label.config(text=f"Khách {user_info} đã đặt ghế {seat_id}", fg="red")
            else:
                self.buttons[seat_id].config(bg="#2ecc71", state="normal") # Màu xanh

# Chạy chương trình
if __name__ == "__main__":
    root = tk.Tk()
    app = CinemaApp(root)
    root.mainloop()