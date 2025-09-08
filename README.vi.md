# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Công cụ **Bot dịch Relay** cho phép dịch và đọc tin nhắn trên Discord sang “ngôn ngữ yêu thích”, cùng với **Giao diện người dùng Desktop (Tkinter)** để điều khiển từ xa và **Console** có thể sử dụng từ terminal. (Tính đến 2025/09/08: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th)
Nhật ký dịch được lưu dưới dạng **JSONL** và có thể chỉ định đường dẫn chia sẻ UNC (ví dụ: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Discord Bot và API HTTP cục bộ (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI**: Chỉnh sửa .env, đăng ký và gửi đến đích, xem nhật ký, **dịch tệp (xem trước trực tiếp)**, tự động khởi động Relay khi ở chế độ cục bộ.
- **Console**: Gắn kết và gửi từ terminal. Hiển thị nhật ký theo dạng tail.

> Những gì cần thiết: **Discord Bot Token** và **OpenAI API Key**.

---

## Cấu trúc (các tệp chính)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Giao diện người dùng Desktop (Tkinter)
IMTB-D_console.py    # Console cho terminal
console_routes.json      # Lưu trữ đích (UI ghi)
log/messages.jsonl       # Nhật ký dịch (JSON Lines)
```

---

## Yêu cầu

- Python 3.10+ (môi trường có thể sử dụng Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (ví dụ tối thiểu)

Tạo tệp `.env` trong thư mục gốc của kho lưu trữ này.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Khuyến nghị sử dụng localhost khi sử dụng cục bộ (UI tự động khởi động Relay)
IMTBD_API_BASE=http://127.0.0.1:8765

# (Tùy chọn) Đường dẫn lưu trữ nhật ký. Windows sử dụng UNC, Linux/mac sử dụng đường dẫn thông thường
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Tùy chọn) Cài đặt dịch
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Khi sử dụng UNC trên Linux/mac, tốt nhất là gắn kết trước và chỉ định bằng đường dẫn thông thường. ※IMTBD_JSONL_PATH **phân biệt chữ hoa chữ thường** (Linux)

---

## Cách sử dụng

### A. Sử dụng UI + Relay cục bộ (ngắn nhất)

```bash
python IMTB-D_ui.py
```

- Nếu `IMTBD_API_BASE` là `http://127.0.0.1:8765` hoặc `localhost`,  
  UI sẽ **tự động hỗ trợ khởi động Relay** (sau khi khởi động sẽ hiển thị "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Chỉnh sửa `.env` từ tab "Setup" và **Lưu .env**.

- Trong tab "Destinations", gán đích (DM/Channel) → nhập văn bản → **Gửi**.
  
  ![destinations.png](docs/images/destinations.png)

- Nhật ký ở phía dưới sẽ phản ánh việc gửi và nhận.
  
  - Khi chọn đích (DM/Channel), nhấp vào "Open Window" → màn hình trò chuyện riêng sẽ mở ra.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Dịch văn bản
    
    - Nhập văn bản vào ô ở dưới cùng của cửa sổ và nhấn gửi hoặc Enter để gửi.
    
    - Nếu cần nhập nhiều dòng, có thể sử dụng Ctrl+Enter để xuống dòng.
  
  - Dịch hình ảnh (Inpaint)
    
    - Kéo và thả hình ảnh để thực hiện dịch hình ảnh theo phương pháp inpaint.
    
    - Hiện tại, chất lượng chưa cao nhưng có thể tham khảo.
      
      Trước khi dịch
      
      ![origin.png](docs/images/origin.png)
      
      Sau khi dịch
      
      ![translated.png](docs/images/translated.png)

### B. Kết nối với Relay từ xa (ví dụ: Raspberry Pi)

- Khởi động `IMTB-D_relay.py` trên máy chủ (Pi, v.v.),
- Cài đặt `IMTBD_API_BASE` trong `.env` của UI thành `http://<server-ip>:8765`.  
- Trong trường hợp này, chức năng Bắt đầu/Dừng của UI sẽ bị vô hiệu hóa và hoạt động ở chế độ **từ xa**.

### C. Console (terminal)

```bash
# Đến kênh
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Đến DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Nhập trực tiếp vào đầu vào chuẩn để gửi (nhật ký sẽ hiển thị theo dạng tail).
```

---

## API (Relay)

- `POST /bind` — Đăng ký tên console và đích (dm/channel, id, lang)  
- `POST /send` — Gửi văn bản đến console đã chỉ định (có thể tạm thời ghi đè bằng `lang`)  
- `POST /send_image` — OCR hình ảnh → dịch → inpaint & vẽ → gửi  
- `GET  /stats` — Trạng thái khởi động và danh sách gán

---

## Nhật ký (JSONL)

- Mặc định: `log/messages.jsonl`. Có thể thay đổi đường dẫn lưu trữ bằng `IMTBD_JSONL_PATH` trong `.env`.  
- UI sẽ theo dõi tệp này và hiển thị trên màn hình. Có thể xem qua chia sẻ UNC.

---

## Câu hỏi thường gặp (FAQ)

**Q: Cách viết đường dẫn UNC trên Windows?**  
A: Trong `.env`, viết `\\raspberrypi\IMTB-D\messages.jsonl` với **hai dấu gạch chéo ngược**.  
   Do yêu cầu escape trong `.env`, thực tế nên viết là `\\\\raspberrypi\\IMTB-D\\messages.jsonl` cho an toàn.

---

## Giấy phép

Giấy phép MIT