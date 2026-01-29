import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 65432

# Tạo 20 ghế: {"1": 0, "2": 0, ...}
seats_status = {str(i): 0 for i in range(1, 21)}
clients = []
lock = threading.Lock()

def broadcast(message):
    data = json.dumps(message).encode('utf-8')
    for client in clients[:]:
        try:
            client.sendall(data)
        except:
            clients.remove(client)

def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")
    clients.append(conn)
    
    # Gửi trạng thái lúc đầu
    conn.sendall(json.dumps({"type": "init", "data": seats_status}).encode('utf-8'))

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
                        print(f"[SUCCESS] Ghe {s_id} da dat")
                        broadcast({"type": "update", "seat_id": s_id, "status": 1})
        except: break
    conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
print("SERVER DANG CHAY...")
while True:
    c, a = s.accept()
    threading.Thread(target=handle_client, args=(c, a), daemon=True).start()