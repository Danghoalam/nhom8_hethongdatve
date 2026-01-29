import socket, tkinter as tk, threading, json
from tkinter import messagebox, ttk

SERVER_IP, PORT = '127.0.0.1', 65432
BG, CARD, RED, GREEN, GOLD, WHITE = "#121212", "#1E1E1E", "#FF5252", "#4CAF50", "#FFD700", "#FFFFFF"

class CinemaApp:
    def __init__(self, root):
        self.root = root; self.root.title("NHÓM 8 - CINEMA SYSTEM")
        self.root.geometry("550x850"); self.root.configure(bg=BG)
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: self.conn.connect((SERVER_IP, PORT))
        except: messagebox.showerror("Lỗi", "Server chưa bật!"); root.destroy()
        self.main_container = tk.Frame(self.root, bg=BG); self.main_container.pack(expand=True, fill="both")
        self.show_login()
        threading.Thread(target=self.receive, daemon=True).start()

    def receive(self):
        while True:
            try:
                raw = self.conn.recv(4096).decode('utf-8'); msg = json.loads(raw)
                if msg['type'] == 'login_ok':
                    self.db_movies, self.db_theaters = msg['movies'], msg['theaters']
                    self.root.after(0, self.show_dashboard)
                elif msg['type'] == 'init_seats': self.root.after(0, self.render_seats, msg['data'])
                elif msg['type'] == 'update_seats': self.handle_realtime(msg)
                elif msg['type'] == 'bill': self.root.after(0, lambda m=msg: messagebox.showinfo("Thành công", f"Ghế: {m['seats']}\nTổng: {m['total']}"))
                elif msg['type'] == 'history_data': self.root.after(0, self.render_history, msg['data'])
            except: break

    def handle_realtime(self, msg):
        if hasattr(self, 'cur_sess') and self.cur_sess['city'] == msg['city'] and \
           self.cur_sess['theater'] == msg['theater'] and self.cur_sess['time'] == msg['time']:
            for s_id in msg['seats']:
                if s_id in self.btns: self.root.after(0, lambda s=s_id: self.btns[s].configure(bg=RED, state="disabled"))

    def clear(self):
        for w in self.main_container.winfo_children(): w.destroy()

    def show_login(self):
        self.clear()
        tk.Label(self.main_container, text="CINEMA", font=("Arial", 30, "bold"), bg=BG, fg=RED).pack(pady=60)
        self.u = tk.Entry(self.main_container, font=("Arial", 14), width=25); self.u.pack(pady=10); self.u.insert(0,"lam")
        self.p = tk.Entry(self.main_container, font=("Arial", 14), width=25, show="*"); self.p.pack(pady=10); self.p.insert(0,"123")
        tk.Button(self.main_container, text="ĐĂNG NHẬP", bg=RED, fg=WHITE, font=("Arial", 12, "bold"), command=lambda: self.conn.send(json.dumps({"type":"login","user":self.u.get(),"pass":self.p.get()}).encode('utf-8'))).pack(pady=30, ipadx=40)

    def show_dashboard(self):
        self.clear()
        tabs = ttk.Notebook(self.main_container)
        self.tab_now = tk.Frame(tabs, bg=BG); self.tab_soon = tk.Frame(tabs, bg=BG); self.tab_hist = tk.Frame(tabs, bg=BG)
        tabs.add(self.tab_now, text=" ĐANG CHIẾU "); tabs.add(self.tab_soon, text=" SẮP CHIẾU "); tabs.add(self.tab_hist, text=" LỊCH SỬ ")
        tabs.pack(fill="both", expand=True)
        self.render_movie_list(self.tab_now, "now"); self.render_movie_list(self.tab_soon, "soon")
        self.conn.send(json.dumps({"type": "get_history"}).encode('utf-8'))

    def render_movie_list(self, parent, status):
        movies = [m for m in self.db_movies if m['status'] == status]
        for m in movies:
            f = tk.Frame(parent, bg=CARD, pady=15); f.pack(fill="x", padx=15, pady=8)
            txt_f = tk.Frame(f, bg=CARD)
            txt_f.pack(side="left", padx=10)
            tk.Label(txt_f, text=m['name'], font=("Arial", 12, "bold"), bg=CARD, fg=GOLD).pack(anchor="w")
            tk.Label(txt_f, text=f"{m['genre']} | {m['duration']}", font=("Arial", 9), bg=CARD, fg="gray").pack(anchor="w")
            tk.Button(f, text="ĐẶT VÉ", bg=RED, fg=WHITE, font=("Arial", 10, "bold"), command=lambda x=m: self.show_booking_options(x)).pack(side="right", padx=15)

    def show_booking_options(self, movie):
        self.selected_movie = movie; self.clear()
        tk.Button(self.main_container, text="← QUAY LẠI", bg=BG, fg=WHITE, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        tk.Label(self.main_container, text=f"LỊCH CHIẾU: {movie['name']}", font=("Arial", 14, "bold"), bg=BG, fg=GOLD).pack(pady=10)
        
        # Tạo vùng có thể cuộn nếu rạp quá dài
        scroll_f = tk.Frame(self.main_container, bg=BG); scroll_f.pack(fill="both", expand=True)
        for city, theaters in self.db_theaters.items():
            tk.Label(scroll_f, text=city, font=("Arial", 12, "bold"), bg="#333", fg=WHITE).pack(fill="x", pady=5)
            for t_name, dates in theaters.items():
                lf = tk.LabelFrame(scroll_f, text=t_name, bg=BG, fg=GOLD, font=("Arial", 10))
                lf.pack(fill="x", padx=20, pady=5)
                for date, times in dates.items():
                    for time, info in times.items():
                        tk.Button(lf, text=f"{time}\n{info['type']}", font=("Arial", 9), command=lambda c=city, t=t_name, d=date, tm=time, p=info['price']: 
                                  self.req_seats(c, t, d, tm, p)).pack(side="left", padx=10, pady=10)

    def req_seats(self, c, t, d, tm, p):
        self.cur_sess = {"city":c, "theater":t, "day":d, "time":tm, "price":p}
        self.conn.send(json.dumps({"type": "get_seats", "city":c, "theater":t, "day":d, "time":tm}).encode('utf-8'))

    def render_seats(self, seats):
        self.clear()
        tk.Button(self.main_container, text="← QUAY LẠI", bg=BG, fg=WHITE, command=lambda: self.show_booking_options(self.selected_movie)).pack(anchor="nw", padx=10)
        tk.Label(self.main_container, text="MÀN HÌNH", bg=WHITE, fg=BG, font=("Arial", 10, "bold")).pack(fill="x", padx=80, pady=25)
        self.sel_s, self.btns = [], {}
        grid = tk.Frame(self.main_container, bg=BG); grid.pack()
        for i, (s_id, stat) in enumerate(seats.items()):
            color = RED if stat == 1 else GREEN
            btn = tk.Button(grid, text=f"G{s_id}", width=6, height=2, bg=color, state="disabled" if stat == 1 else "normal", command=lambda x=s_id: self.toggle(x))
            btn.grid(row=i//4, column=i%4, padx=8, pady=8); self.btns[s_id] = btn
        tk.Button(self.main_container, text="XÁC NHẬN THANH TOÁN", bg=GOLD, font=("Arial", 12, "bold"), command=self.confirm).pack(pady=40, ipadx=20)

    def toggle(self, s_id):
        if s_id in self.sel_s: self.sel_s.remove(s_id); self.btns[s_id].config(bg=GREEN)
        else: self.sel_s.append(s_id); self.btns[s_id].config(bg=WHITE)

    def confirm(self):
        if not self.sel_s: return
        tot = len(self.sel_s) * self.cur_sess['price']
        self.conn.send(json.dumps({"type": "book", **self.cur_sess, "seats": self.sel_s, "movie": self.selected_movie['name'], "total": f"{tot:,} VND"}).encode('utf-8'))
        self.show_dashboard()

    def render_history(self, history):
        for w in self.tab_hist.winfo_children(): w.destroy()
        if not history: tk.Label(self.tab_hist, text="Chưa có lịch sử.", bg=BG, fg="gray").pack(pady=20)
        for h in history:
            f = tk.Frame(self.tab_hist, bg=CARD, pady=10); f.pack(fill="x", padx=15, pady=5)
            tk.Label(f, text=f"🎬 {h['movie']}\n📍 {h['theater']} | {h['time']}\n🎟️ Ghế: {h['seats']} - {h['total']}", bg=CARD, fg=WHITE, justify="left").pack(side="left", padx=10)

if __name__ == "__main__":
    root = tk.Tk(); app = CinemaApp(root); root.mainloop()