import socket, threading, json

DB_FILE = 'database.json'
clients = []

def load_db():
    with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

def broadcast_update(city, theater, day, time, seats):
    msg = json.dumps({"type": "update_seats", "city": city, "theater": theater, "day": day, "time": time, "seats": seats})
    for c in clients:
        try: c.send(msg.encode('utf-8'))
        except: clients.remove(c)

def handle_client(conn, addr):
    clients.append(conn)
    user_now = None
    while True:
        try:
            raw = conn.recv(4096).decode('utf-8')
            if not raw: break
            req = json.loads(raw)
            db = load_db()

            if req['type'] == 'login':
                u, p = req['user'], req['pass']
                if u in db['users'] and db['users'][u] == p:
                    user_now = u
                    conn.send(json.dumps({"type": "login_ok", "movies": db['movies'], "theaters": db['theaters']}).encode('utf-8'))
                else: conn.send(json.dumps({"type": "login_fail"}).encode('utf-8'))

            elif req['type'] == 'get_seats':
                c, th, d, tm = req['city'], req['theater'], req['day'], req['time']
                seats = db['theaters'].get(c, {}).get(th, {}).get(d, {}).get(tm, {}).get('seats', {})
                conn.send(json.dumps({"type": "init_seats", "data": seats}).encode('utf-8'))

            elif req['type'] == 'book':
                c, th, d, tm, s_list = req['city'], req['theater'], req['day'], req['time'], req['seats']
                target = db['theaters'][c][th][d][tm]['seats']
                for s in s_list: target[s] = 1
                if user_now not in db['history']: db['history'][user_now] = []
                db['history'][user_now].append({"movie": req['movie'], "theater": th, "time": f"{tm} ({d})", "seats": s_list, "total": req['total']})
                save_db(db)
                conn.send(json.dumps({"type": "bill", "seats": s_list, "total": req['total']}).encode('utf-8'))
                broadcast_update(c, th, d, tm, s_list)

            elif req['type'] == 'get_history':
                h = db['history'].get(user_now, [])
                conn.send(json.dumps({"type": "history_data", "data": h}).encode('utf-8'))
        except: break
    if conn in clients: clients.remove(conn)
    conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 65432))
server.listen()
print("SERVER CINEMA READY...")
while True:
    c, a = server.accept()
    threading.Thread(target=handle_client, args=(c, a), daemon=True).start()