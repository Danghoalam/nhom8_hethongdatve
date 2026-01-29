import socket
import threading
import json
import sqlite3
import os

HOST = '127.0.0.1'
PORT = 65432
DB_NAME = "cinema.db"

# --- XỬ LÝ DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, is_admin INTEGER)''')
    # Bảng Movies
    c.execute('''CREATE TABLE IF NOT EXISTS movies 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price INTEGER, 
                  time TEXT, room TEXT, poster TEXT, trailer TEXT)''')
    # Bảng Bookings (Lưu ghế đã đặt)
    c.execute('''CREATE TABLE IF NOT EXISTS bookings 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, movie_id INTEGER, 
                  seat_index INTEGER, combo_pop INTEGER, combo_water INTEGER, total_price INTEGER)''')
    
    # Thêm dữ liệu mẫu nếu chưa có
    c.execute("SELECT count(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES ('admin', '123', 1)") # Admin mặc định
        c.execute("INSERT INTO users VALUES ('khach', '123', 0)") # Khách mặc định
        
    c.execute("SELECT count(*) FROM movies")
    if c.fetchone()[0] == 0:
        # Dữ liệu phim mẫu
        c.execute("INSERT INTO movies (title, price, time, room, poster, trailer) VALUES (?,?,?,?,?,?)",
                  ("Mai (2024)", 100000, "18:00", "Rạp 1", "mai.jpg", "https://www.youtube.com/watch?v=example1"))
        c.execute("INSERT INTO movies (title, price, time, room, poster, trailer) VALUES (?,?,?,?,?,?)",
                  ("Đào, Phở và Piano", 80000, "20:00", "Rạp 2", "dao.png", "https://www.youtube.com/watch?v=example2"))
        c.execute("INSERT INTO movies (title, price, time, room, poster, trailer) VALUES (?,?,?,?,?,?)",
                  ("Kung Fu Panda 4", 120000, "19:30", "Rạp 3", "panda.png", "https://www.youtube.com/watch?v=example3"))
        
    conn.commit()
    conn.close()
    print("Database initialized.")

# --- XỬ LÝ CLIENT ---
def handle_client(conn, addr):
    print(f"Connected: {addr}")
    try:
        while True:
            data = conn.recv(4096)
            if not data: break
            
            req = json.loads(data.decode('utf-8'))
            cmd = req.get('command')
            resp = {'status': 'fail', 'message': 'Unknown command'}
            
            db = sqlite3.connect(DB_NAME) 
            c = db.cursor()

            if cmd == 'LOGIN':
                user = req.get('username')
                pwd = req.get('password')
                c.execute("SELECT is_admin FROM users WHERE username=? AND password=?", (user, pwd))
                row = c.fetchone()
                if row:
                    resp = {'status': 'success', 'is_admin': row[0]}
                else:
                    resp = {'status': 'fail', 'message': 'Sai tài khoản hoặc mật khẩu!'}

            elif cmd == 'REGISTER':
                user = req.get('username')
                pwd = req.get('password')
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, 0)", (user, pwd))
                    db.commit()
                    resp = {'status': 'success', 'message': 'Đăng ký thành công!'}
                except:
                    resp = {'status': 'fail', 'message': 'Tài khoản đã tồn tại!'}

            elif cmd == 'GET_MOVIES':
                c.execute("SELECT * FROM movies")
                cols = [description[0] for description in c.description]
                movies = [dict(zip(cols, row)) for row in c.fetchall()]
                movies_dict = {str(m['id']): m for m in movies}
                resp = {'status': 'success', 'data': movies_dict}

            elif cmd == 'GET_SEATS':
                m_id = req.get('movie_id')
                c.execute("SELECT seat_index FROM bookings WHERE movie_id=?", (m_id,))
                taken_seats = [r[0] for r in c.fetchall()]
                seats_status = [0] * 20
                for idx in taken_seats:
                    if 0 <= idx < 20:
                        seats_status[idx] = 1
                resp = {'status': 'success', 'seats': seats_status}

            elif cmd == 'BOOK_SEAT':
                m_id = req.get('movie_id')
                seat_idx = req.get('seat_index')
                user = req.get('username')
                c.execute("SELECT * FROM bookings WHERE movie_id=? AND seat_index=?", (m_id, seat_idx))
                if c.fetchone():
                    resp = {'status': 'fail', 'message': 'Ghế này vừa bị người khác đặt mất rồi!'}
                else:
                    c.execute("INSERT INTO bookings (user, movie_id, seat_index, combo_pop, combo_water, total_price) VALUES (?,?,?,?,?,?)",
                              (user, m_id, seat_idx, req.get('pop'), req.get('water'), req.get('total')))
                    db.commit()
                    resp = {'status': 'success', 'message': 'Đặt vé thành công!'}

            elif cmd == 'GET_HISTORY':
                user = req.get('username')
                c.execute('''SELECT b.id, m.title, b.seat_index, b.total_price 
                             FROM bookings b JOIN movies m ON b.movie_id = m.id 
                             WHERE b.user=? ORDER BY b.id DESC''', (user,))
                hist = [{'id': r[0], 'title': r[1], 'seat': r[2], 'price': r[3]} for r in c.fetchall()]
                resp = {'status': 'success', 'data': hist}

            # --- [TÍNH NĂNG MỚI] ADMIN XEM TOÀN BỘ LỊCH SỬ ---
            elif cmd == 'GET_ALL_HISTORY':
                c.execute('''SELECT b.id, b.user, m.title, b.seat_index, b.total_price 
                             FROM bookings b JOIN movies m ON b.movie_id = m.id 
                             ORDER BY b.id DESC''')
                all_hist = [{'id': r[0], 'user': r[1], 'title': r[2], 'seat': r[3], 'price': r[4]} for r in c.fetchall()]
                resp = {'status': 'success', 'data': all_hist}

            elif cmd == 'ADD_MOVIE':
                c.execute("INSERT INTO movies (title, price, time, room, poster, trailer) VALUES (?,?,?,?,?,?)",
                          (req['title'], req['price'], req['time'], req['room'], req['poster'], req['trailer']))
                db.commit()
                resp = {'status': 'success', 'message': 'Thêm phim thành công!'}

            db.close()
            conn.sendall(json.dumps(resp).encode('utf-8'))
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def start_server():
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server chạy tại {HOST}:{PORT} (SQLite Mode)")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()