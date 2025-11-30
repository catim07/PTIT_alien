# ALIEN INVASION - TÀU ROCKET SIÊU CHÍNH XÁC

Một game bắn súng 2D thú vị được phát triển bằng Pygame. Người chơi điều khiển tàu rocket để bảo vệ trái đất khỏi những cuộc tấn công của người ngoài hành tinh.

## 🎮 Tính năng

- **4 cấp độ chơi** với độ khó tăng dần
- **Hệ thống cấp bậc** - mở khóa các ải khi hoàn thành
- **Bản boss cuối cùng** - ải 4 có boss với nhiều chiêu thức tấn công
- **Lưu trữ dữ liệu** - lưu điểm cao nhất và ải đã mở khóa
- **Cài đặt âm thanh** - điều chỉnh âm lượng nhạc và hiệu ứng âm thanh
- **Toàn màn hình** - hỗ trợ chế độ toàn màn hình
- **Hỗ trợ tiếng Việt** - tất cả giao diện bằng tiếng Việt

## Yêu cầu

- Python 3.8 trở lên
- Pygame

## Cách chạy game

### Windows
Mở terminal và chạy dòng lệnh  python src/alien_invasion.py

### macOS / Linux
Mở terminal và chạy dòng lệnh  python src/alien_invasion.py

## Hướng dẫn chơi

### Điều khiển
- **Mũi tên trái/phải** hoặc **A/D**: Di chuyển tàu
- **Space bar**: Bắn
- **ESC hoặc nút MENU**: Tạm dừng game

### Các ải
1. **Ải 1: Bắt đầu** - Dễ, dành cho người mới bắt đầu
2. **Ải 2: Sóng lớn** - Trung bình, alien di chuyển nhanh hơn
3. **Ải 3: Boss cuối** - Khó, 25 alien di chuyển ngẫu nhiên
4. **Ải 4: Hủy diệt** - Cực khó, đối mặt với boss lớn

### Hệ thống điểm
- Tiêu diệt alien nhân lên điểm số của nó
- Hoàn thành một ải nhận bonus
- Hoàn thành tất cả các ải để xem điểm cao nhất của bạn

## Cài đặt

Trước khi chạy, hãy cài đặt các phụ thuộc:

```bash
pip install -r requirements.txt
```

## Cấu trúc thư mục

```
gamepy/
├── src/
│   ├── alien_invasion_main.py    # File chính của game
│   ├── menu.py                   # Menu chính
│   ├── level_menu.py             # Menu chọn ải
│   ├── menu_pause.py             # Menu tạm dừng
│   ├── settings_menu.py          # Menu cài đặt
│   ├── save_manager.py           # Quản lý lưu trữ dữ liệu
│   ├── audio_manager.py          # Quản lý âm thanh
│   ├── font_helper.py            # Hỗ trợ font tiếng Việt
│   ├── backgrounds/              # Ảnh nền game
│   └── sounds/                   # File âm thanh
├── README.md                     # File này
├── requirements.txt              # Danh sách phụ thuộc
└── save_data.json               # Dữ liệu lưu trữ (tự động tạo)
```

## Cài đặt trong game

- **Âm lượng**: Điều chỉnh từ 0% đến 100%
- **Toàn màn hình**: Bật/tắt chế độ toàn màn hình
- **Lưu dữ liệu tự động**: Game tự động lưu điểm cao nhất và ải đã mở

## Khắc phục sự cố

### Không thể chạy game
- Đảm bảo Python đã được cài đặt: `python --version`
- Cài đặt Pygame: `pip install pygame`

### Chữ Việt hiển thị sai
- Game tự động chọn font hệ thống hỗ trợ tiếng Việt
- Nếu vấn đề vẫn xảy ra, cài đặt font Segoe UI hoặc Arial Unicode MS

### Không nghe thấy âm thanh
- Kiểm tra thư mục `src/sounds/` có file `.wav`
- Kiểm tra âm lượng trong cài đặt game (tối thiểu 10%)
- Đảm bảo âm thanh hệ thống không bị tắt

**Chúc bạn chơi vui vẻ!**
