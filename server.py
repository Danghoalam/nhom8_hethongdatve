import socket
import threading
import json

HOST = '0.0.0.0' # Cho phép mọi máy trong mạng kết nối
PORT = 65432

# Khởi tạo 20 ghế trống (0: trống, 1: đã đặt)
seats_status = {str(i): 0 for i in range(1, 21)}
clients = []
lock = threading.Lock()

def broadcast(message):
    """Gửi dữ liệu đến tất cả các máy đang kết nối"""
    data = json.dumps(message).encode('utf-8')
    for client in clients[:]:
        try:
            client.sendall(data)
        except:
            clients.remove(client)

def handle_client(conn, addr):
    user_label = f"{addr[0]}:{addr[1]}"
    print(f"[CONNECTED] {user_label} đã kết nối.")
    clients.append(conn)
    
    # Gửi trạng thái ghế hiện tại cho người mới vào
    try:
        conn.sendall(json.dumps({"type": "init", "data": seats_status}).encode('utf-8'))
    except:
        pass

    while True:
        try:
            raw = conn.recv(1024).decode('utf-8')
            if not raw: break
            msg = json.loads(raw)
            
            if msg['type'] == 'book':
                s_id = str(msg['seat_id'])
                with lock:
                    if seats_status[s_id] == 0:
                        seats_status[s_id] = 1
                        print(f"[BOOKED] Ghế {s_id} được đặt bởi {user_label}")
                        # Phát tin cho tất cả bao gồm ID ghế và thông tin người đặt
                        broadcast({
                            "type": "update", 
                            "seat_id": s_id, 
                            "status": 1, 
                            "user": user_label
                        })
        except:
            break
    
    print(f"[DISCONNECTED] {user_label} đã thoát.")
    conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
print(f"SERVER ĐANG CHẠY TRÊN PORT {PORT}...")

while True:
    c, a = s.accept()
    threading.Thread(target=handle_client, args=(c, a), daemon=True).start()