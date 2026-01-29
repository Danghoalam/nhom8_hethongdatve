import socket
import threading
import json
import os

HOST = '0.0.0.0'
PORT = 65432
DB_FILE = 'database.json'

# Khóa để tránh ghi file cùng lúc
lock = threading.Lock()

def load_db():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

clients = [] # Lưu danh sách (conn, current_room)

def broadcast(message, room=None):
    data = json.dumps(message).encode('utf-8')
    for client_conn, client_room in clients:
        if room is None or client_room == room:
            try:
                client_conn.sendall(data)
            except:
                pass

def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")
    current_user = None
    current_room = None
    
    while True:
        try:
            raw = conn.recv(1024).decode('utf-8')
            if not raw: break
            msg = json.loads(raw)
            db = load_db()

            # 1. Xử lý Đăng nhập
            if msg['type'] == 'login':
                u, p = msg['user'], msg['pass']
                if db['users'].get(u) == p:
                    current_user = u
                    conn.sendall(json.dumps({"type": "login_ok", "rooms": list(db['rooms'].keys())}).encode('utf-8'))
                    clients.append([conn, None])
                else:
                    conn.sendall(json.dumps({"type": "login_fail"}).encode('utf-8'))

            # 2. Xử lý Chọn phòng
            elif msg['type'] == 'join_room':
                current_room = msg['room']
                for c in clients:
                    if c[0] == conn: c[1] = current_room
                conn.sendall(json.dumps({"type": "init", "data": db['rooms'][current_room]}).encode('utf-8'))

            # 3. Xử lý Đặt vé & Hóa đơn
            elif msg['type'] == 'book':
                s_id = str(msg['seat_id'])
                room = msg['room']
                with lock:
                    db = load_db()
                    if db['rooms'][room][s_id] == 0:
                        db['rooms'][room][s_id] = 1
                        save_db(db)
                        # Gửi hóa đơn cho người đặt
                        bill = {"type": "bill", "seat": s_id, "price": "50.000 VND", "user": current_user}
                        conn.sendall(json.dumps(bill).encode('utf-8'))
                        # Cập nhật cho mọi người trong phòng
                        broadcast({"type": "update", "seat_id": s_id, "user": current_user}, room=room)
        except:
            break
    conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
print("SERVER ĐANG CHẠY...")
while True:
    c, a = s.accept()
    threading.Thread(target=handle_client, args=(c, a), daemon=True).start()