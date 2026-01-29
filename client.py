import socket
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import json

SERVER_IP = '127.0.0.1'
PORT = 65432

# Cấu hình màu sắc hiện đại
COLOR_BG = "#1A1A1D"       # Nền tối
COLOR_CARD = "#4E4E50"     # Màu khung
COLOR_PRIMARY = "#E74C3C"  # Đỏ (Màu nhấn/Ghế đã đặt)
COLOR_SUCCESS = "#2ECC71"  # Xanh lá (Ghế trống)
COLOR_TEXT = "#FFFFFF"     # Chữ trắng

class CinemaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NHÓM 8 - CINEMA BOOKING")
        self.root.geometry("450x650")
        self.root.configure(bg=COLOR_BG)
        
        self.current_room = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.client_socket.connect((SERVER_IP, PORT))
            threading.Thread(target=self.receive_data, daemon=True).start()
        except:
            messagebox.showerror("Lỗi", "Không thể kết nối đến Server!")
            self.root.destroy()

        self.main_container = tk.Frame(self.root, bg=COLOR_BG)
        self.main_container.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.show_login()

    def clear_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # --- MÀN HÌNH 1: ĐĂNG NHẬP ---
    def show_login(self):
        self.clear_screen()
        
        tk.Label(self.main_container, text="WELCOME BACK", font=("Segoe UI", 20, "bold"), 
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(pady=(40, 10))
        tk.Label(self.main_container, text="Đăng nhập để đặt vé ngay", font=("Segoe UI", 10), 
                 bg=COLOR_BG, fg="gray").pack(pady=(0, 30))

        # Khung nhập liệu
        entry_frame = tk.Frame(self.main_container, bg=COLOR_BG)
        entry_frame.pack(fill="x", padx=30)

        tk.Label(entry_frame, text="Username", bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w")
        self.u_entry = tk.Entry(entry_frame, font=("Segoe UI", 12), bg=COLOR_CARD, fg=COLOR_TEXT, insertbackground="white", borderwidth=0)
        self.u_entry.pack(fill="x", pady=(5, 15), ipady=8)

        tk.Label(entry_frame, text="Password", bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w")
        self.p_entry = tk.Entry(entry_frame, font=("Segoe UI", 12), bg=COLOR_CARD, fg=COLOR_TEXT, show="*", insertbackground="white", borderwidth=0)
        self.p_entry.pack(fill="x", pady=(5, 30), ipady=8)

        tk.Button(entry_frame, text="LOGIN", command=self.send_login, bg=COLOR_PRIMARY, fg=COLOR_TEXT, 
                  font=("Segoe UI", 12, "bold"), borderwidth=0, cursor="hand2", activebackground="#C0392B").pack(fill="x", ipady=10)

    def send_login(self):
        data = {"type": "login", "user": self.u_entry.get(), "pass": self.p_entry.get()}
        self.client_socket.sendall(json.dumps(data).encode('utf-8'))

    # --- MÀN HÌNH 2: CHỌN PHÒNG ---
    def show_room_selection(self, rooms):
        self.clear_screen()
        tk.Label(self.main_container, text="SELECT ROOM", font=("Segoe UI", 18, "bold"), 
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(pady=30)
        
        for room in rooms:
            btn = tk.Button(self.main_container, text=room, font=("Segoe UI", 12), width=25,
                      bg=COLOR_CARD, fg=COLOR_TEXT, borderwidth=0, cursor="hand2",
                      activebackground=COLOR_PRIMARY, command=lambda r=room: self.join_room(r))
            btn.pack(pady=10, ipady=15)

    def join_room(self, room):
        self.current_room = room
        self.client_socket.sendall(json.dumps({"type": "join_room", "room": room}).encode('utf-8'))

    # --- MÀN HÌNH 3: ĐẶT VÉ ---
    def show_seats(self, data):
        self.clear_screen()
        
        # Header phòng chiếu
        header = tk.Frame(self.main_container, bg=COLOR_BG)
        header.pack(fill="x")
        tk.Button(header, text="←", command=lambda: self.send_login(), bg=COLOR_BG, fg="white", borderwidth=0).pack(side="left")
        tk.Label(header, text=self.current_room, font=("Segoe UI", 14, "bold"), bg=COLOR_BG, fg=COLOR_TEXT).pack(side="left", padx=10)

        # Màn hình (Screen) giả lập
        tk.Label(self.main_container, text="SCREEN", bg=COLOR_CARD, fg="lightgray", font=("Arial", 8)).pack(fill="x", pady=(20, 30))
        
        self.info_lbl = tk.Label(self.main_container, text="Vui lòng chọn ghế trống", bg=COLOR_BG, fg="gray", font=("Segoe UI", 9, "italic"))
        self.info_lbl.pack(pady=(0, 10))
        
        grid_frame = tk.Frame(self.main_container, bg=COLOR_BG)
        grid_frame.pack()

        self.btns = {}
        for s_id, status in data.items():
            color = COLOR_PRIMARY if status == 1 else COLOR_SUCCESS
            state = "disabled" if status == 1 else "normal"
            btn = tk.Button(grid_frame, text=s_id, width=6, height=2, bg=color, fg=COLOR_TEXT, 
                            font=("Segoe UI", 9, "bold"), borderwidth=0, state=state,
                            command=lambda s=s_id: self.send_book(s))
            btn.grid(row=(int(s_id)-1)//4, column=(int(s_id)-1)%4, padx=6, pady=6)
            self.btns[s_id] = btn

        # Chú thích
        legend = tk.Frame(self.main_container, bg=COLOR_BG)
        legend.pack(pady=20)
        tk.Label(legend, text="■ Trống", fg=COLOR_SUCCESS, bg=COLOR_BG).pack(side="left", padx=10)
        tk.Label(legend, text="■ Đã đặt", fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left", padx=10)

    def send_book(self, s_id):
        self.client_socket.sendall(json.dumps({"type": "book", "seat_id": s_id, "room": self.current_room}).encode('utf-8'))

    # --- XỬ LÝ NHẬN DỮ LIỆU ---
    def receive_data(self):
        while True:
            try:
                raw = self.client_socket.recv(1024).decode('utf-8')
                msg = json.loads(raw)
                if msg['type'] == 'login_ok':
                    self.root.after(0, self.show_room_selection, msg['rooms'])
                elif msg['type'] == 'login_fail':
                    messagebox.showerror("Lỗi", "Tài khoản hoặc mật khẩu không chính xác!")
                elif msg['type'] == 'init':
                    self.root.after(0, self.show_seats, msg['data'])
                elif msg['type'] == 'update':
                    self.root.after(0, self.update_seat, msg['seat_id'], msg['user'])
                elif msg['type'] == 'bill':
                    messagebox.showinfo("XÁC NHẬN ĐẶT VÉ", f"Đặt thành công!\nGhế: {msg['seat']}\nTổng tiền: {msg['price']}\nKhách hàng: {msg['user']}")
            except: break

    def update_seat(self, s_id, user):
        if s_id in self.btns:
            self.btns[s_id].config(bg=COLOR_PRIMARY, state="disabled")
            self.info_lbl.config(text=f"Khách {user} vừa đặt ghế {s_id}", fg=COLOR_PRIMARY)

if __name__ == "__main__":
    root = tk.Tk()
    app = CinemaApp(root)
    root.mainloop()