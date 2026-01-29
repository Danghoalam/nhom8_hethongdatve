import socket
import json
import tkinter as tk
from tkinter import messagebox, Toplevel, simpledialog
from tkinter import ttk # [MỚI] Thư viện để vẽ bảng (Table)
from PIL import Image, ImageTk 
import os
import webbrowser 

HOST = '127.0.0.1'
PORT = 65432

# --- BẢNG MÀU MODERN DARK ---
COLOR_BG = "#141414"           
COLOR_CARD = "#1f1f1f"         
COLOR_ACCENT = "#E50914"       
COLOR_HOVER = "#b00710"        
COLOR_TEXT = "#FFFFFF"         
COLOR_TEXT_SUB = "#B3B3B3"     
COLOR_VIP = "#DBA506"          

class CinemaClient:
    def __init__(self, root):
        self.root = root
        self.root.title("CGV CINEMA PREMIUM")
        self.root.geometry("1200x850")
        self.root.configure(bg=COLOR_BG)
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
        except:
            messagebox.showerror("Lỗi", "Không thể kết nối Server! Hãy chạy server.py trước.")
            root.destroy()
            return

        self.username = None
        self.is_admin = 0
        self.movies_data = {}

        self.show_login_screen()

    def send_request(self, data):
        try:
            self.client_socket.sendall(json.dumps(data).encode('utf-8'))
            return json.loads(self.client_socket.recv(8192).decode('utf-8')) # Tăng buffer để nhận nhiều dữ liệu
        except:
            return {}

    # --- TIỆN ÍCH TẠO NÚT ĐẸP ---
    def create_button(self, parent, text, cmd, bg=COLOR_ACCENT, width=15, font=("Helvetica", 10, "bold")):
        btn = tk.Button(parent, text=text, bg=bg, fg="white", font=font, 
                        relief="flat", activebackground=COLOR_HOVER, activeforeground="white",
                        cursor="hand2", command=cmd, width=width, pady=8)
        btn.bind("<Enter>", lambda e: btn.config(bg=COLOR_HOVER if bg == COLOR_ACCENT else "#666"))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    # --- 1. LOGIN ---
    def show_login_screen(self):
        self.clear_window()
        bg_frame = tk.Frame(self.root, bg=COLOR_BG)
        bg_frame.pack(fill=tk.BOTH, expand=True)

        login_frame = tk.Frame(bg_frame, bg="black", padx=60, pady=60)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Frame(login_frame, bg=COLOR_ACCENT, height=2).pack(fill=tk.X, pady=(0, 20))

        tk.Label(login_frame, text="ĐĂNG NHẬP", font=("Helvetica", 24, "bold"), fg=COLOR_TEXT, bg="black").pack(pady=(0, 30))

        tk.Label(login_frame, text="Tài khoản", font=("Arial", 10), fg=COLOR_TEXT_SUB, bg="black").pack(anchor="w")
        entry_user = tk.Entry(login_frame, width=35, font=("Arial", 12), bg="#333", fg="white", relief="flat", insertbackground="white")
        entry_user.pack(pady=(5, 20), ipady=5)

        tk.Label(login_frame, text="Mật khẩu", font=("Arial", 10), fg=COLOR_TEXT_SUB, bg="black").pack(anchor="w")
        entry_pwd = tk.Entry(login_frame, show="•", width=35, font=("Arial", 12), bg="#333", fg="white", relief="flat", insertbackground="white")
        entry_pwd.pack(pady=(5, 30), ipady=5)

        def login():
            u, p = entry_user.get(), entry_pwd.get()
            resp = self.send_request({'command': 'LOGIN', 'username': u, 'password': p})
            if resp.get('status') == 'success':
                self.username = u
                self.is_admin = resp.get('is_admin', 0)
                self.show_main_interface()
            else:
                messagebox.showerror("Oops", resp.get('message'))

        def register():
            u, p = entry_user.get(), entry_pwd.get()
            if not u or not p: return messagebox.showwarning("!", "Vui lòng nhập thông tin!")
            resp = self.send_request({'command': 'REGISTER', 'username': u, 'password': p})
            messagebox.showinfo("Thông báo", resp.get('message'))

        self.create_button(login_frame, "ĐĂNG NHẬP NGAY", login, width=30).pack(pady=5)
        tk.Button(login_frame, text="Chưa có tài khoản? Đăng ký", bg="black", fg="#999", 
                  relief="flat", cursor="hand2", font=("Arial", 9, "underline"),
                  command=register).pack(pady=10)

    # --- 2. GIAO DIỆN CHÍNH ---
    def show_main_interface(self):
        self.clear_window()
        
        header = tk.Frame(self.root, bg="black", height=70, padx=20)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="CGV CINEMAS", font=("Impact", 28), fg=COLOR_ACCENT, bg="black").pack(side=tk.LEFT)
        
        user_panel = tk.Frame(header, bg="black")
        user_panel.pack(side=tk.RIGHT)
        
        tk.Label(user_panel, text=f"Hi, {self.username}", font=("Arial", 12, "bold"), fg="white", bg="black").pack(side=tk.LEFT, padx=15)
        
        # --- [TÍNH NĂNG MỚI] NÚT CHO ADMIN ---
        if self.is_admin:
            tk.Button(user_panel, text="QUẢN LÝ VÉ", bg=COLOR_VIP, fg="black", font=("Arial", 9, "bold"),
                      relief="flat", command=self.show_all_history).pack(side=tk.LEFT, padx=5)
            tk.Button(user_panel, text="+ ADMIN ADD", bg="#333", fg="white", font=("Arial", 9, "bold"),
                      relief="flat", command=self.admin_add_movie).pack(side=tk.LEFT, padx=5)
        # --------------------------------------

        tk.Button(user_panel, text="LỊCH SỬ CÁ NHÂN", bg="#333", fg="white", font=("Arial", 9), relief="flat",
                  command=self.show_history).pack(side=tk.LEFT, padx=5)
        tk.Button(user_panel, text="LOGOUT", bg=COLOR_ACCENT, fg="white", font=("Arial", 9, "bold"), relief="flat",
                  command=self.show_login_screen).pack(side=tk.LEFT, padx=5)

        tk.Frame(self.root, bg="#333", height=1).pack(fill=tk.X)

        container_outer = tk.Frame(self.root, bg=COLOR_BG)
        container_outer.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        tk.Label(container_outer, text="PHIM ĐANG CHIẾU / NOW SHOWING", font=("Arial", 16, "bold"), 
                 fg="white", bg=COLOR_BG).pack(anchor="w", pady=(0, 20))

        self.movie_grid = tk.Frame(container_outer, bg=COLOR_BG)
        self.movie_grid.pack(fill=tk.BOTH, expand=True)
        
        self.load_movies()

    def load_movies(self):
        for w in self.movie_grid.winfo_children(): w.destroy()
        resp = self.send_request({'command': 'GET_MOVIES'})
        self.movies_data = resp.get('data', {})
        
        r, c = 0, 0
        MAX_COL = 4
        for m_id, info in self.movies_data.items():
            self.create_movie_card(m_id, info, r, c)
            c += 1
            if c >= MAX_COL:
                c = 0
                r += 1

    def create_movie_card(self, m_id, info, r, c):
        card = tk.Frame(self.movie_grid, bg=COLOR_CARD, padx=10, pady=10)
        card.grid(row=r, column=c, padx=15, pady=15, sticky="nsew")
        
        def on_enter(e): card.config(bg="#333")
        def on_leave(e): card.config(bg=COLOR_CARD)
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            img_path = os.path.join(base_path, info['poster'])
            if os.path.exists(img_path):
                raw_img = Image.open(img_path).resize((180, 270))
                img = ImageTk.PhotoImage(raw_img)
                lbl = tk.Label(card, image=img, bg=COLOR_CARD)
                lbl.image = img
                lbl.pack()
            else:
                tk.Label(card, text="NO POSTER", width=22, height=16, bg="#000", fg="#555").pack()
        except: pass

        tk.Label(card, text=info['title'].upper(), font=("Arial", 11, "bold"), fg="white", bg=COLOR_CARD, wraplength=180).pack(pady=(10, 5))
        tk.Label(card, text=f"{info['time']} | {info['room']}", font=("Arial", 9), fg=COLOR_TEXT_SUB, bg=COLOR_CARD).pack()
        tk.Label(card, text=f"{info['price']:,} đ", font=("Arial", 12, "bold"), fg=COLOR_VIP, bg=COLOR_CARD).pack(pady=5)

        btn_row = tk.Frame(card, bg=COLOR_CARD)
        btn_row.pack(pady=10)

        if info.get('trailer'):
            tk.Button(btn_row, text="▶ Trailer", font=("Arial", 8), bg="#333", fg="white", relief="flat",
                      command=lambda: webbrowser.open(info['trailer'])).pack(side=tk.LEFT, padx=5)

        self.create_button(btn_row, "ĐẶT VÉ", lambda: self.open_booking(m_id), width=10, font=("Arial", 9, "bold")).pack(side=tk.LEFT)

    # --- 3. ĐẶT VÉ ---
    def open_booking(self, m_id):
        curr_movie = self.movies_data[m_id]
        bw = Toplevel(self.root)
        bw.title(f"BOOKING: {curr_movie['title']}")
        bw.geometry("1100x700")
        bw.configure(bg=COLOR_BG)

        main = tk.Frame(bw, bg=COLOR_BG)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        left = tk.Frame(main, bg=COLOR_BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        screen_cv = tk.Canvas(left, width=600, height=80, bg=COLOR_BG, highlightthickness=0)
        screen_cv.pack(pady=(0, 30))
        screen_cv.create_polygon(50, 10, 550, 10, 500, 70, 100, 70, fill="#333", outline="#555")
        screen_cv.create_text(300, 40, text="MÀN HÌNH / SCREEN", fill="white", font=("Arial", 10, "bold"))

        seat_container = tk.Frame(left, bg=COLOR_BG)
        seat_container.pack()

        legend = tk.Frame(left, bg=COLOR_BG)
        legend.pack(pady=20)
        def draw_legend(txt, col):
            f = tk.Frame(legend, bg=COLOR_BG); f.pack(side=tk.LEFT, padx=10)
            tk.Label(f, bg=col, width=2, height=1).pack(side=tk.LEFT)
            tk.Label(f, text=txt, fg="white", bg=COLOR_BG, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        draw_legend("Thường", "white")
        draw_legend("VIP", COLOR_VIP)
        draw_legend("Đang chọn", COLOR_ACCENT)
        draw_legend("Đã bán", "#333")

        right = tk.Frame(main, bg="#1a1a1a", width=350, padx=20, pady=20)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        right.pack_propagate(False)

        tk.Label(right, text=curr_movie['title'], font=("Helvetica", 18, "bold"), fg="white", bg="#1a1a1a", wraplength=300, justify="left").pack(anchor="w")
        tk.Label(right, text=f"{curr_movie['time']} | {curr_movie['room']}", fg="#888", bg="#1a1a1a").pack(anchor="w", pady=(0, 20))
        tk.Frame(right, bg="#333", height=1).pack(fill=tk.X, pady=10)

        self.var_pop = tk.IntVar()
        self.var_wat = tk.IntVar()
        
        def create_chk(txt, var):
            c = tk.Checkbutton(right, text=txt, variable=var, bg="#1a1a1a", fg="white", selectcolor="#333", 
                               activebackground="#1a1a1a", activeforeground="white", font=("Arial", 11),
                               command=lambda: update_total())
            c.pack(anchor="w", pady=5)
            return c

        create_chk("Bắp Rang Bơ (50.000đ)", self.var_pop)
        create_chk("Nước Ngọt (20.000đ)", self.var_wat)

        tk.Frame(right, bg="#333", height=1).pack(fill=tk.X, pady=20)

        lbl_seat_info = tk.Label(right, text="Chưa chọn ghế", fg="#aaa", bg="#1a1a1a", justify="left")
        lbl_seat_info.pack(anchor="w")

        lbl_total = tk.Label(right, text="0 đ", font=("Helvetica", 24, "bold"), fg=COLOR_ACCENT, bg="#1a1a1a")
        lbl_total.pack(pady=20, anchor="e")

        self.selected_seat = tk.IntVar(value=-1)

        def update_total():
            s_idx = self.selected_seat.get()
            total = 0
            detail = ""
            
            if s_idx != -1:
                r, _ = divmod(s_idx, 5)
                is_vip = r >= 2
                seat_price = curr_movie['price'] + (20000 if is_vip else 0)
                total += seat_price
                type_str = "VIP" if is_vip else "STD"
                detail = f"Ghế: {s_idx+1} ({type_str})\nGiá vé: {seat_price:,} đ"
            
            if self.var_pop.get(): total += 50000
            if self.var_wat.get(): total += 20000
            
            lbl_seat_info.config(text=detail if detail else "Vui lòng chọn ghế trên màn hình")
            lbl_total.config(text=f"{total:,} đ")
            return total

        def refresh_seats():
            for w in seat_container.winfo_children(): w.destroy()
            resp = self.send_request({'command': 'GET_SEATS', 'movie_id': m_id})
            seats = resp.get('seats', [])
            
            for i, status in enumerate(seats):
                r, c = divmod(i, 5)
                is_vip = r >= 2
                bg_color = "white"
                fg_color = "black"
                if is_vip: bg_color = COLOR_VIP
                
                if status == 1: 
                    tk.Label(seat_container, text="X", bg="#333", fg="#555", width=6, height=3, relief="flat").grid(row=r, column=c, padx=6, pady=6)
                else:
                    btn = tk.Radiobutton(seat_container, text=f"{i+1}", variable=self.selected_seat, value=i, 
                                   indicatoron=0, width=6, height=3, 
                                   bg=bg_color, fg=fg_color, selectcolor=COLOR_ACCENT, 
                                   activebackground=COLOR_HOVER, borderwidth=0,
                                   command=update_total)
                    btn.grid(row=r, column=c, padx=6, pady=6)
                    if c == 4 and is_vip:
                        tk.Label(seat_container, text="VIP", bg=COLOR_BG, fg=COLOR_VIP, font=("Arial", 7)).grid(row=r, column=5, sticky="w")

        def confirm_pay():
            t = update_total()
            if self.selected_seat.get() == -1: return messagebox.showwarning("!", "Vui lòng chọn ghế!")
            
            resp = self.send_request({
                'command': 'BOOK_SEAT', 'movie_id': m_id, 'seat_index': self.selected_seat.get(),
                'username': self.username, 'pop': self.var_pop.get(), 'water': self.var_wat.get(), 'total': t
            })
            
            if resp['status'] == 'success':
                try:
                    with open(f"ticket_{self.username}_{m_id}.txt", "w", encoding="utf-8") as f:
                        f.write(f"--- VÉ XEM PHIM CGV ---\nPhim: {curr_movie['title']}\nGhế: {self.selected_seat.get()+1}\nTổng: {t:,} đ\nCảm ơn quý khách!")
                except: pass
                messagebox.showinfo("Thành công", f"Thanh toán thành công: {t:,} đ\nVé đã được xuất ra file!")
                bw.destroy()
            else:
                messagebox.showerror("Lỗi", resp['message'])
                refresh_seats()

        self.create_button(right, "THANH TOÁN", confirm_pay, width=20, font=("Arial", 12, "bold")).pack(side=tk.BOTTOM)
        refresh_seats()

    # --- 4. TÍNH NĂNG ADMIN MỚI (Bảng quản lý) ---
    def show_all_history(self):
        # Yêu cầu Server gửi dữ liệu vé của TẤT CẢ mọi người
        resp = self.send_request({'command': 'GET_ALL_HISTORY'})
        if resp.get('status') != 'success': return

        data = resp.get('data', [])

        win = Toplevel(self.root)
        win.title("QUẢN LÝ ĐẶT VÉ (ADMIN)")
        win.geometry("900x500")
        win.configure(bg=COLOR_BG)
        
        tk.Label(win, text="DANH SÁCH VÉ ĐÃ ĐẶT TOÀN HỆ THỐNG", font=("Arial", 16, "bold"), fg=COLOR_ACCENT, bg=COLOR_BG).pack(pady=10)

        # Sử dụng Treeview để tạo bảng
        cols = ("ID", "Khách hàng", "Phim", "Ghế", "Giá vé")
        tree = ttk.Treeview(win, columns=cols, show='headings', height=15)
        
        tree.heading("ID", text="ID")
        tree.column("ID", width=50, anchor="center")
        
        tree.heading("Khách hàng", text="Khách hàng")
        tree.column("Khách hàng", width=150)
        
        tree.heading("Phim", text="Tên Phim")
        tree.column("Phim", width=300)
        
        tree.heading("Ghế", text="Ghế số")
        tree.column("Ghế", width=80, anchor="center")
        
        tree.heading("Giá vé", text="Tổng tiền")
        tree.column("Giá vé", width=120, anchor="e")

        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        total_revenue = 0
        for item in data:
            tree.insert("", tk.END, values=(item['id'], item['user'], item['title'], item['seat']+1, f"{item['price']:,}"))
            total_revenue += item['price']
            
        tk.Label(win, text=f"TỔNG DOANH THU: {total_revenue:,} VNĐ", font=("Arial", 14, "bold"), fg=COLOR_VIP, bg=COLOR_BG).pack(pady=10)

    # --- CÁC HÀM PHỤ KHÁC ---
    def show_history(self):
        resp = self.send_request({'command': 'GET_HISTORY', 'username': self.username})
        win = Toplevel(self.root)
        win.title("Lịch sử giao dịch"); win.geometry("500x400")
        win.configure(bg=COLOR_BG)
        lb = tk.Listbox(win, font=("Courier", 10), bg="#1f1f1f", fg="white", relief="flat", height=15)
        lb.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        for item in resp.get('data', []):
            lb.insert(tk.END, f" {item['title']:<20} | Ghế: {item['seat']+1:<3} | {item['price']:,} đ")

    def admin_add_movie(self):
        title = simpledialog.askstring("Admin", "Tên phim:")
        if not title: return
        price = simpledialog.askinteger("Admin", "Giá vé (VNĐ):", initialvalue=100000)
        poster = simpledialog.askstring("Admin", "File ảnh (vd: mai.jpg):")
        trailer = simpledialog.askstring("Admin", "Link Trailer:")
        self.send_request({'command': 'ADD_MOVIE', 'title': title, 'price': price, 'time': '20:00', 'room': 'New Room', 'poster': poster, 'trailer': trailer})
        messagebox.showinfo("Admin", "Đã thêm phim mới!")
        self.load_movies()

    def clear_window(self):
        for w in self.root.winfo_children(): w.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CinemaClient(root)
    root.mainloop()