import json

def reset():
    data = {
        "users": {
            "lam": "123",
            "nhom8": "123456"
        },
        "rooms": {
            "Phòng 01": {str(i): 0 for i in range(1, 11)},
            "Phòng 02": {str(i): 0 for i in range(1, 11)}
        }
    }
    with open('database.json', 'w') as f:
        json.dump(data, f, indent=4)
    print("Đã reset toàn bộ ghế về màu xanh!")

if __name__ == "__main__":
    reset()