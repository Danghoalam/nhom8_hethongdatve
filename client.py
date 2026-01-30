import socket, tkinter as tk, threading, json
from tkinter import messagebox, ttk
from PIL import Image, ImageTk  # Thêm dòng này để xử lý ảnh
# --- CẤU HÌNH KẾT NỐI ---
SERVER_IP, PORT = '127.0.0.1', 65432

# --- BẢNG MÀU PHONG CÁCH CGV ---
COLOR_BG = "#151515"          # Nền tối chủ đạo
COLOR_CARD = "#222222"        # Nền các thẻ/khung
COLOR_ACCENT = "#E71A0F"      # Màu đỏ thương hiệu (Nút chính)
COLOR_HOVER = "#C4160C"       # Màu đỏ đậm khi di chuột
COLOR_TEXT_MAIN = "#FFFFFF"   # Chữ trắng
COLOR_TEXT_SEC = "#AAAAAA"    # Chữ phụ (màu xám)
COLOR_GOLD = "#FDC02F"        # Màu vàng kim (Tiêu đề/Giá)
COLOR_SEAT_AVAIL = "#333333"  # Ghế trống
COLOR_SEAT_SOLD = "#B71C1C"   # Ghế đã bán
COLOR_SEAT_SEL = "#4CAF50"    # Ghế đang chọn

class CinemaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CGV CINEMAS - BOOKING SYSTEM")
        self.root.geometry("600x900")
        self.root.configure(bg=COLOR_BG)
        
        # Cấu hình style cho Tabs (Notebook)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR_CARD, foreground=COLOR_TEXT_MAIN, padding=[20, 10], font=("Arial", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", COLOR_ACCENT)], foreground=[("selected", COLOR_TEXT_MAIN)])

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.conn.connect((SERVER_IP, PORT))
        except:
            messagebox.showerror("Lỗi Kết Nối", "Không thể kết nối đến Server!\nVui lòng kiểm tra lại server.")
            root.destroy()
            return

        self.main_container = tk.Frame(self.root, bg=COLOR_BG)
        self.main_container.pack(expand=True, fill="both", padx=0, pady=0)
        
        self.show_login()
        threading.Thread(target=self.receive, daemon=True).start()

    def receive(self):
        while True:
            try:
                raw = self.conn.recv(4096).decode('utf-8')
                if not raw: break
                msg = json.loads(raw)

                if msg['type'] == 'login_ok':
                    self.db_movies, self.db_theaters = msg['movies'], msg['theaters']
                    self.root.after(0, self.show_dashboard)
                elif msg['type'] == 'login_fail':
                    self.root.after(0, lambda: messagebox.showerror("Thất bại", "Sai tài khoản hoặc mật khẩu!"))
                elif msg['type'] == 'init_seats':
                    self.root.after(0, self.render_seats, msg['data'])
                elif msg['type'] == 'update_seats':
                    self.handle_realtime(msg)
                elif msg['type'] == 'bill':
                    self.root.after(0, lambda m=msg: self.show_bill_success(m))
                elif msg['type'] == 'history_data':
                    self.root.after(0, self.render_history, msg['data'])
            except:
                break

    def handle_realtime(self, msg):
        # Cập nhật ghế theo thời gian thực nếu đang ở đúng phòng chiếu đó
        if hasattr(self, 'cur_sess') and \
           self.cur_sess['city'] == msg['city'] and \
           self.cur_sess['theater'] == msg['theater'] and \
           self.cur_sess['time'] == msg['time']:
            for s_id in msg['seats']:
                if s_id in self.btns:
                    self.root.after(0, lambda s=s_id: self.update_seat_ui(s))

    def update_seat_ui(self, s_id):
        if s_id in self.btns:
            self.btns[s_id].configure(bg=COLOR_SEAT_SOLD, state="disabled", text="X")

    def show_bill_success(self, m):
        messagebox.showinfo("Đặt Vé Thành Công", f"Đã đặt thành công các ghế: {m['seats']}\nTổng thanh toán: {m['total']}")
    
    def clear(self):
        for w in self.main_container.winfo_children(): w.destroy()

    # --- HELPER: TẠO NÚT ĐẸP ---
    def create_btn(self, parent, text, cmd, bg=COLOR_ACCENT, fg=COLOR_TEXT_MAIN, width=None):
        btn = tk.Button(parent, text=text, bg=bg, fg=fg, font=("Arial", 11, "bold"), 
                        activebackground=COLOR_HOVER, activeforeground=COLOR_TEXT_MAIN,
                        relief="flat", borderwidth=0, cursor="hand2", command=cmd)
        if width: btn.config(width=width)
        return btn

    # --- HELPER: XỬ LÝ GIÁ TIỀN ---
    def parse_price(self, p):
        """Chuyển đổi giá tiền từ int hoặc string sang int an toàn"""
        if isinstance(p, int):
            return p
        if isinstance(p, str):
            # Xóa các ký tự không phải số
            clean_str = p.replace("k", "000").replace(".", "").replace(",", "").replace(" VND", "").replace(" đ", "")
            try:
                return int(clean_str)
            except ValueError:
                return 0
        return 0

    def format_currency(self, amount):
        """Định dạng số thành tiền tệ (VD: 150,000 đ)"""
        return f"{amount:,} đ".replace(",", ".")

    # --- MÀN HÌNH LOGIN ---
    def show_login(self):
        self.clear()
        
        login_frame = tk.Frame(self.main_container, bg=COLOR_CARD, padx=40, pady=40)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Logo Text
        tk.Label(login_frame, text="CGV CINEMAS", font=("Impact", 32), bg=COLOR_CARD, fg=COLOR_ACCENT).pack(pady=(0, 10))
        tk.Label(login_frame, text="MEMBER LOGIN", font=("Arial", 10, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_SEC).pack(pady=(0, 30))

        # Inputs
        tk.Label(login_frame, text="Tài khoản", font=("Arial", 10), bg=COLOR_CARD, fg=COLOR_TEXT_MAIN).pack(anchor="w")
        self.u = tk.Entry(login_frame, font=("Arial", 14), bg="#333", fg="white", insertbackground="white", relief="flat", justify="center")
        self.u.pack(pady=5, ipadx=5, ipady=5)
        self.u.insert(0, "lam")

        tk.Label(login_frame, text="Mật khẩu", font=("Arial", 10), bg=COLOR_CARD, fg=COLOR_TEXT_MAIN).pack(anchor="w", pady=(15,0))
        self.p = tk.Entry(login_frame, font=("Arial", 14), bg="#333", fg="white", insertbackground="white", relief="flat", show="*", justify="center")
        self.p.pack(pady=5, ipadx=5, ipady=5)
        self.p.insert(0, "123")

        # Button Login
        self.create_btn(login_frame, "ĐĂNG NHẬP", self.send_login).pack(pady=30, fill="x", ipady=5)

    def send_login(self):
        self.conn.send(json.dumps({"type":"login","user":self.u.get(),"pass":self.p.get()}).encode('utf-8'))

    # --- DASHBOARD CHÍNH ---
    def show_dashboard(self):
        self.clear()
        
        # Header
        header = tk.Frame(self.main_container, bg=COLOR_BG, pady=15)
        header.pack(fill="x")
        tk.Label(header, text="  TRANG CHỦ", font=("Arial", 18, "bold"), bg=COLOR_BG, fg=COLOR_GOLD).pack(side="left")
        tk.Button(header, text="Đăng xuất", bg=COLOR_BG, fg=COLOR_TEXT_SEC, borderwidth=0, font=("Arial", 10),
                  command=self.show_login, cursor="hand2").pack(side="right", padx=15)

        # Tabs
        tabs = ttk.Notebook(self.main_container)
        self.tab_now = tk.Frame(tabs, bg=COLOR_BG); self.tab_soon = tk.Frame(tabs, bg=COLOR_BG); self.tab_hist = tk.Frame(tabs, bg=COLOR_BG)
        tabs.add(self.tab_now, text=" PHIM ĐANG CHIẾU ")
        tabs.add(self.tab_soon, text=" PHIM SẮP CHIẾU ")
        tabs.add(self.tab_hist, text=" LỊCH SỬ ĐẶT VÉ ")
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.render_movie_list(self.tab_now, "now")
        self.render_movie_list(self.tab_soon, "soon")
        self.conn.send(json.dumps({"type": "get_history"}).encode('utf-8'))

    def render_movie_list(self, parent, status):
        # Tạo canvas để scroll nếu danh sách dài
        canvas = tk.Canvas(parent, bg=COLOR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_f = tk.Frame(canvas, bg=COLOR_BG)

        scroll_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_f, anchor="nw", width=550) # Fix width xấp xỉ geometry
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        movies = [m for m in self.db_movies if m['status'] == status]
        if not movies:
            tk.Label(scroll_f, text="Không có phim nào.", bg=COLOR_BG, fg="gray").pack(pady=20)
            return

        for m in movies:
            # Movie Card
            card = tk.Frame(scroll_f, bg=COLOR_CARD, pady=10, padx=10)
            card.pack(fill="x", padx=10, pady=5)
            
            # --- ĐOẠN SỬA: CHÈN FILE poster1.jpg ---
            try:
                from PIL import Image, ImageTk
                # Mở file poster1.jpg
                img_open = Image.open("poster1.jpg")
                # Chỉnh kích thước cho khớp với ô (Rộng 80, Cao 110 là đẹp nhất)
                img_resized = img_open.resize((80, 110), Image.Resampling.LANCZOS)
                img_final = ImageTk.PhotoImage(img_resized)
                
                # Tạo Label chứa ảnh thay vì chữ "POSTER"
                poster = tk.Label(card, image=img_final, bg=COLOR_CARD)
                poster.image = img_final  # Dòng này bắt buộc phải có để ảnh hiển thị
            except Exception as e:
                # Nếu không tìm thấy file poster1.jpg thì hiện ô xám dự phòng
                poster = tk.Label(card, text="🎬", bg="#444", fg="#777", width=10, height=6, font=("Arial", 12))
            
            poster.pack(side="left", padx=(0, 15))
            # --------------------------------------

            # Thông tin (Giữ nguyên phần cũ của Lâm)
            info_f = tk.Frame(card, bg=COLOR_CARD)
            info_f.pack(side="left", fill="both", expand=True)
            
            tk.Label(info_f, text=m['name'].upper(), font=("Arial", 14, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MAIN, wraplength=350, justify="left").pack(anchor="w")
            tk.Label(info_f, text=f"Thể loại: {m['genre']}", font=("Arial", 10), bg=COLOR_CARD, fg=COLOR_TEXT_SEC).pack(anchor="w", pady=2)
            tk.Label(info_f, text=f"Thời lượng: {m['duration']}", font=("Arial", 10), bg=COLOR_CARD, fg=COLOR_TEXT_SEC).pack(anchor="w")

            # Nút đặt vé
            self.create_btn(card, "ĐẶT VÉ", lambda x=m: self.show_booking_options(x), width=10).pack(side="right", padx=10)

    # --- CHỌN SUẤT CHIẾU ---
    def show_booking_options(self, movie):
        self.selected_movie = movie
        self.clear()
        
        # Header Nav
        nav = tk.Frame(self.main_container, bg=COLOR_BG)
        nav.pack(fill="x", pady=10)
        tk.Button(nav, text="❮ QUAY LẠI", bg=COLOR_BG, fg=COLOR_TEXT_SEC, borderwidth=0, font=("Arial", 11), 
                 command=self.show_dashboard, cursor="hand2").pack(side="left", padx=10)
        
        # Movie Info Header
        tk.Label(self.main_container, text=movie['name'], font=("Arial", 20, "bold"), bg=COLOR_BG, fg=COLOR_GOLD, wraplength=500).pack(pady=10)
        tk.Label(self.main_container, text="Vui lòng chọn Rạp & Suất chiếu", font=("Arial", 12), bg=COLOR_BG, fg="gray").pack(pady=(0, 20))

        # Scroll container
        canvas = tk.Canvas(self.main_container, bg=COLOR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.main_container, orient="vertical", command=canvas.yview)
        scroll_f = tk.Frame(canvas, bg=COLOR_BG)
        
        scroll_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scroll_f, anchor="nw")
        
        # Auto-resize width
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', configure_canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")

        # Logic hiển thị rạp
        for city, theaters in self.db_theaters.items():
            tk.Label(scroll_f, text=f"📍 {city}", font=("Arial", 14, "bold"), bg=COLOR_BG, fg=COLOR_TEXT_MAIN).pack(anchor="w", pady=(20, 5))
            
            for t_name, dates in theaters.items():
                t_frame = tk.Frame(scroll_f, bg=COLOR_CARD, padx=15, pady=15)
                t_frame.pack(fill="x", pady=5)
                
                tk.Label(t_frame, text=t_name, font=("Arial", 12, "bold"), bg=COLOR_CARD, fg=COLOR_ACCENT).pack(anchor="w")
                
                for date, times in dates.items():
                    d_row = tk.Frame(t_frame, bg=COLOR_CARD)
                    d_row.pack(fill="x", pady=5)
                    tk.Label(d_row, text=f"Ngày: {date}", font=("Arial", 10, "italic"), bg=COLOR_CARD, fg="gray").pack(anchor="w")
                    
                    # Time Grid
                    time_grid = tk.Frame(t_frame, bg=COLOR_CARD)
                    time_grid.pack(fill="x", pady=5)
                    
                    for time, info in times.items():
                        # Lấy giá và format
                        price_val = self.parse_price(info['price'])
                        price_str = self.format_currency(price_val)
                        
                        btn_txt = f"{time}\n{info['type']}\n{price_str}"
                        b = tk.Button(time_grid, text=btn_txt, font=("Arial", 9), bg="#333", fg="white", 
                                      activebackground=COLOR_GOLD, activeforeground="black",
                                      relief="flat", width=14, height=3,
                                      command=lambda c=city, t=t_name, d=date, tm=time, p=info['price']: 
                                      self.req_seats(c, t, d, tm, p))
                        b.pack(side="left", padx=5, pady=5)

    def req_seats(self, c, t, d, tm, p):
        self.cur_sess = {"city":c, "theater":t, "day":d, "time":tm, "price":p}
        self.conn.send(json.dumps({"type": "get_seats", "city":c, "theater":t, "day":d, "time":tm}).encode('utf-8'))

    # --- SƠ ĐỒ GHẾ ---
    def render_seats(self, seats):
        self.clear()
        
        # Header
        nav = tk.Frame(self.main_container, bg=COLOR_BG)
        nav.pack(fill="x", pady=10)
        tk.Button(nav, text="❮ QUAY LẠI", bg=COLOR_BG, fg=COLOR_TEXT_SEC, borderwidth=0, 
                  command=lambda: self.show_booking_options(self.selected_movie)).pack(side="left", padx=10)
        
        # Screen Info
        info_f = tk.Frame(self.main_container, bg=COLOR_BG)
        info_f.pack(pady=5)
        tk.Label(info_f, text=f"{self.cur_sess['theater']}", font=("Arial", 12, "bold"), bg=COLOR_BG, fg=COLOR_GOLD).pack()
        tk.Label(info_f, text=f"{self.cur_sess['time']} | {self.cur_sess['day']}", font=("Arial", 10), bg=COLOR_BG, fg="white").pack()

        # Visual Screen
        screen_cv = tk.Canvas(self.main_container, width=400, height=40, bg=COLOR_BG, highlightthickness=0)
        screen_cv.pack(pady=(20, 10))
        # Vẽ hình thang giả lập màn hình
        screen_cv.create_polygon(20, 0, 380, 0, 360, 30, 40, 30, fill="#555", outline="")
        screen_cv.create_text(200, 15, text="MÀN HÌNH", fill="white", font=("Arial", 8, "bold"))

        # Seats Grid
        self.sel_s, self.btns = [], {}
        grid_frame = tk.Frame(self.main_container, bg=COLOR_BG)
        grid_frame.pack(pady=10)

        # Chú thích
        legend = tk.Frame(self.main_container, bg=COLOR_BG)
        legend.pack(pady=10)
        self.create_legend_item(legend, COLOR_SEAT_AVAIL, "Trống").pack(side="left", padx=10)
        self.create_legend_item(legend, COLOR_SEAT_SEL, "Đang chọn").pack(side="left", padx=10)
        self.create_legend_item(legend, COLOR_SEAT_SOLD, "Đã bán").pack(side="left", padx=10)

        # Render Loop
        sorted_seats = sorted(seats.items(), key=lambda x: int(x[0])) # Sắp xếp ghế theo số
        for i, (s_id, stat) in enumerate(sorted_seats):
            color = COLOR_SEAT_SOLD if stat == 1 else COLOR_SEAT_AVAIL
            state = "disabled" if stat == 1 else "normal"
            text_disp = "X" if stat == 1 else s_id

            btn = tk.Button(grid_frame, text=text_disp, width=4, height=1, bg=color, fg="white",
                            font=("Arial", 9, "bold"), relief="flat", state=state,
                            command=lambda x=s_id: self.toggle(x))
            
            # Giả lập khoảng cách lối đi (layout 4-4-4)
            col_gap = 10 if (i % 4 == 0 and i != 0 and i % 12 != 0) else 2 
            
            # Xếp 4 ghế 1 hàng -> sửa thành 6 ghế hoặc tùy biến. Ở đây mình để mặc định 4 ghế/hàng cho giống layout cũ
            row = i // 4
            col = i % 4
            
            btn.grid(row=row, column=col, padx=2, pady=4)
            self.btns[s_id] = btn

        # Footer Action
        self.btn_pay = self.create_btn(self.main_container, "THANH TOÁN (0 đ)", self.confirm)
        self.btn_pay.pack(side="bottom", fill="x", padx=20, pady=20, ipady=5)

    def create_legend_item(self, parent, color, text):
        f = tk.Frame(parent, bg=COLOR_BG)
        tk.Frame(f, width=15, height=15, bg=color).pack(side="left", padx=5)
        tk.Label(f, text=text, bg=COLOR_BG, fg="gray", font=("Arial", 9)).pack(side="left")
        return f

    def toggle(self, s_id):
        if s_id in self.sel_s:
            self.sel_s.remove(s_id)
            self.btns[s_id].config(bg=COLOR_SEAT_AVAIL)
        else:
            self.sel_s.append(s_id)
            self.btns[s_id].config(bg=COLOR_SEAT_SEL)
        
        # --- SỬA LỖI: Xử lý giá tiền (int/str) ---
        price_val = self.parse_price(self.cur_sess['price'])
        
        total = len(self.sel_s) * price_val
        self.btn_pay.config(text=f"THANH TOÁN ({self.format_currency(total)})")

    def confirm(self):
        if not self.sel_s:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ghế!")
            return
        
        # --- SỬA LỖI: Tính toán lại tổng tiền để gửi ---
        price_val = self.parse_price(self.cur_sess['price'])
        total_val = len(self.sel_s) * price_val
        total_str = self.format_currency(total_val)

        self.conn.send(json.dumps({
            "type": "book",
            **self.cur_sess,
            "seats": self.sel_s,
            "movie": self.selected_movie['name'],
            "total": total_str
        }).encode('utf-8'))
        
        self.show_dashboard()

    # --- LỊCH SỬ ---
    def render_history(self, history):
        for w in self.tab_hist.winfo_children(): w.destroy()
        
        canvas = tk.Canvas(self.tab_hist, bg=COLOR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.tab_hist, orient="vertical", command=canvas.yview)
        scroll_f = tk.Frame(canvas, bg=COLOR_BG)
        
        scroll_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_f, anchor="nw", width=550)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not history:
            tk.Label(scroll_f, text="Bạn chưa có lịch sử đặt vé nào.", bg=COLOR_BG, fg="gray").pack(pady=20)
            return

        for h in history:
            # Ticket Style Look
            f = tk.Frame(scroll_f, bg=COLOR_CARD, pady=10, padx=10)
            f.pack(fill="x", padx=10, pady=5)
            
            # Left Stripe (Red)
            tk.Frame(f, bg=COLOR_ACCENT, width=4).pack(side="left", fill="y", padx=(0, 10))
            
            content = tk.Frame(f, bg=COLOR_CARD)
            content.pack(side="left", fill="both", expand=True)
            
            tk.Label(content, text=h['movie'], font=("Arial", 12, "bold"), bg=COLOR_CARD, fg=COLOR_GOLD, wraplength=300, justify="left").pack(anchor="w")
            tk.Label(content, text=f"{h['theater']}  •  {h['time']}", bg=COLOR_CARD, fg="white", font=("Arial", 10)).pack(anchor="w", pady=2)
            
            # Xử lý hiển thị ghế (list hoặc string)
            seats_str = h['seats']
            if isinstance(seats_str, list): seats_str = ", ".join(seats_str)
            
            tk.Label(content, text=f"Ghế: {seats_str}", bg=COLOR_CARD, fg=COLOR_ACCENT, font=("Arial", 10, "bold")).pack(anchor="w")
            
            tk.Label(f, text=h['total'], font=("Arial", 11, "bold"), bg=COLOR_CARD, fg="white").pack(side="right", padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = CinemaApp(root)
    root.mainloop()