import json

def reset_database():
    # 1. Định nghĩa nội dung ban đầu dựa trên cấu trúc file Lâm gửi
    data = {
        "users": {
            "lam": "123",
            "nhom8": "123456"
        },
        "movies": [
            {
                "id": "m1",
                "status": "now",
                "name": "RUNNING MAN VIỆT NAM MÙA 3 - CON RỐI TỰ DO",
                "genre": "Hành động",
                "duration": "180p",
                "age": "C13",
                "lang": "Phụ đề"
            },
            {
                "id": "m2",
                "status": "soon",
                "name": "TIỂU YÊU QUÁI NÚI LÃNG LÃNG",
                "genre": "Viễn tưởng",
                "duration": "192p",
                "age": "C16",
                "lang": "Lồng tiếng"
            }
        ],
        "theaters": {
            "Hồ Chí Minh": {
                "Cinema Quận 1": {
                    "2026-02-01": {
                        "18:00": {"type": "IMAX", "price": 150000, "seats": {str(i): 0 for i in range(1, 13)}},
                        "20:00": {"type": "2D", "price": 90000, "seats": {str(i): 0 for i in range(1, 13)}}
                    }
                },
                "Cinema Thủ Đức": {
                    "2026-02-01": {
                        "19:00": {"type": "2D", "price": 85000, "seats": {str(i): 0 for i in range(1, 13)}}
                    }
                },
                "Cinema Tân Bình": {
                    "2026-02-01": {
                        "17:00": {"type": "4DX", "price": 180000, "seats": {str(i): 0 for i in range(1, 13)}}
                    }
                }
            },
            "Hà Nội": {
                "Cinema Ba Đình": {
                    "2026-02-01": {
                        "18:30": {"type": "IMAX", "price": 160000, "seats": {str(i): 0 for i in range(1, 13)}}
                    }
                },
                "Cinema Cầu Giấy": {
                    "2026-02-01": {
                        "20:15": {"type": "2D", "price": 95000, "seats": {str(i): 0 for i in range(1, 13)}}
                    }
                }
            }
        },
        "history": {
            "lam": [],
            "nhom8": []
        }
    }

    # 2. Ghi đè vào file database.json
    try:
        with open('database.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("✅ Đã reset toàn bộ ghế và lịch sử đặt vé thành công!")
    except Exception as e:
        print(f"❌ Lỗi khi ghi file: {e}")

if __name__ == "__main__":
    reset_database()