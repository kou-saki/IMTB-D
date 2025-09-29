## Công cụ Dịch Đa Ngôn Ngữ Tương Tác cho Discord (IMTB-D)

Công cụ bao gồm **Bot Dịch Relay** cho phép dịch và viết tin nhắn trên Discord sang “ngôn ngữ yêu thích”, **Giao diện Người Dùng Máy Tính để Bàn (Tkinter)** để điều khiển từ xa, và **Console** có thể sử dụng từ terminal.  
Nhật ký dịch có thể được lưu dưới dạng **JSONL** và có thể chỉ định đường dẫn chia sẻ UNC (ví dụ: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Discord Bot và API HTTP cục bộ (`/bind`, `/send`, `/send_image`, `/stats`)

- **Thêm Relay r3**: **`/translate`** (nhận văn bản qua HTTP và trả về **bản dịch qua HTTP**)

- **UI**: Chỉnh sửa .env, đăng ký và gửi đến đích, xem nhật ký, **dịch tệp (xem trước trực tiếp)**, tự động khởi động Relay khi ở chế độ cục bộ

- **Console**: Liên kết và gửi từ terminal. Hiển thị nhật ký theo dạng tail

> Những gì cần thiết: **Discord Bot Token** và **OpenAI API Key** (cấu hình không gọi trực tiếp OpenAI cũng được)

---

## Mục Lục

- [Cấu hình](#%E6%A7%8B%E6%88%90)

- [Yêu cầu](#%E8%A6%81%E4%BB%B6)

- [.env (ví dụ tối thiểu)](#env%E6%9C%80%E5%B0%8F%E4%BE%8B)

- [Cách sử dụng](#%E4%BD%BF%E3%81%84%E6%96%B9)
  
  - [A. Sử dụng UI + Relay cục bộ](#a-%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E3%81%A7-ui--relay)
  
  - [B. Kết nối với Relay từ xa](#b-%E3%83%AA%E3%83%A2%E3%83%BC%E3%83%88-relay-%E3%81%AB%E6%8E%A5%E7%B6%9A)
  
  - [C. Console (terminal)](#c-console%E3%82%BF%E3%83%BC%E3%83%9F%E3%83%8A%E3%83%AB)

- [API (Relay)](#apirelay)
  
  - [/translate (r3 mới)](#translater3-%E6%96%B0%E8%A6%8F)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [Nhật ký (JSONL)](#%E3%83%AD%E3%82%B0jsonl)

- [Ví dụ tích hợp với VS Code Wrapper](#vs-code-%E3%83%A9%E3%83%83%E3%83%91%E3%83%BC%E9%80%A3%E6%90%BA%E4%BE%8B)

- [Câu hỏi thường gặp](#%E3%82%88%E3%81%8F%E3%81%82%E3%82%8B%E8%B3%AA%E5%95%8F)

- [Mẹo phát triển/vận hành](#%E9%96%8B%E7%99%BA%E9%81%8B%E7%94%A8tips)

- [Giấy phép](#%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9)

---

## Cấu hình (tệp chính)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Giao diện Người Dùng Máy Tính để Bàn (Tkinter)
IMTB-D_console.py    # Console cho terminal
console_routes.json      # Lưu trữ đích (UI ghi)
log/messages.jsonl       # Nhật ký dịch (JSON Lines)
```

---

## Yêu cầu

- Tải xuống các tệp chính
- Python 3.10+ (môi trường có thể sử dụng Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (ví dụ tối thiểu)

Tạo tệp `.env` ngay dưới thư mục của kho lưu trữ này.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# URL cơ sở của Relay (khuyến nghị 127.0.0.1 khi vận hành cục bộ UI)
IMTBD_API_BASE=http://127.0.0.1:8765

# Cài đặt Relay Bind (Listen) (nếu không được cài đặt, mặc định: 127.0.0.1:8765)
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# (Tùy chọn) Đường dẫn lưu nhật ký dịch
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Tùy chọn) Liên quan đến dịch
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Khi sử dụng UNC trên Linux/mac, tốt nhất là gắn kết trước và chỉ định bằng đường dẫn thông thường. *Lưu ý IMTBD_JSONL_PATH là **phân biệt chữ hoa chữ thường** (Linux)*

---

## Cách sử dụng

### A. Sử dụng UI + Relay cục bộ (ngắn nhất)

```bash
python IMTB-D_ui.py
```

- Nếu `IMTBD_API_BASE` là `http://127.0.0.1:8765` hoặc `localhost`,  
  UI sẽ **tự động hỗ trợ khởi động Relay** (sau khi khởi động sẽ hiển thị “API ready”).
  
  ![setup.png](docs/images/setup.png)
  
  Chỉnh sửa `.env` từ tab “Setup” và **Lưu .env**.

- Trong tab “Destinations”, **Bind** đến đích (DM/Channel) → Nhập văn bản → **Gửi**.
  
  ![destinations.png](docs/images/destinations.png)

- Nhật ký ở dưới sẽ phản ánh việc gửi và nhận.
  
  - Khi đã chọn đích (DM/Channel), nhấp vào “Open Window” → màn hình trò chuyện riêng sẽ mở ra.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Dịch văn bản
    
    - Nhập văn bản vào ô ở dưới cùng của cửa sổ và nhấn gửi hoặc Enter để gửi.
    
    - Nếu cần nhập nhiều dòng, có thể sử dụng Ctrl+Enter để xuống dòng.
  
  - Dịch Hình ảnh (Inpaint)
    
    - Kéo và thả hình ảnh để thực hiện dịch hình ảnh theo phương pháp inpaint.
    
    - Hiện tại, chất lượng chưa cao nhưng có thể tham khảo.
      
      Trước khi dịch
      
      ![origin.png](docs/images/origin.png)
      
      Sau khi dịch
      
      ![translated.png](docs/images/translated.png)

### B. Kết nối với Relay từ xa (ví dụ: Raspberry Pi)

- Khởi động `IMTB-D_relay.py` trên máy chủ (Pi, v.v.),
- Cài đặt `IMTBD_API_BASE` trong `.env` của UI thành `http://<server-ip>:8765`.  
- Trong trường hợp này, chức năng Bắt Đầu/Dừng của UI sẽ bị vô hiệu hóa và hoạt động ở chế độ **từ xa**.

### C. Console (terminal)

```bash
# Đến kênh
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Đến DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Nhập trực tiếp vào đầu vào chuẩn sẽ gửi (nhật ký sẽ hiển thị theo dạng tail).
```

---

## API (Relay)

### `/translate` (r3 mới)

**API tổng quát nhận văn bản qua HTTP và trả về bản dịch qua HTTP**. Không đi qua Discord.

- **POST** `/translate`

- **Request (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""` (không chỉ định/auto/rỗng sẽ tự động xác định bên trong)
  
  - `target`: mặc định là `DEFAULT_REPLY_LANG` trong `.env` (ví dụ: `"ja"`)

- **Response (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **Ví dụ: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **Ví dụ: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### Cam kết về giá trị trả về

- Khi `ok` là `true`, `translated` sẽ chứa bản dịch

- Khi thất bại sẽ trả về `{ "ok": false, "error": "<message>" }` (HTTP 4xx/5xx)

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — Đăng ký tên console và đích (dm/channel, id, lang, v.v.)

- `POST /send` — Gửi văn bản đến console đã chỉ định (gửi đến Discord)

- `POST /send_image` — Hình ảnh OCR → dịch → inpaint → gửi

- `GET /stats` — Trạng thái khởi động và danh sách binding> `/translate` là **phản hồi trực tiếp cho HTTP client**, vì vậy rất phù hợp cho việc tích hợp với các công cụ bên ngoài như VS Code. Quy trình qua Discord truyền thống sử dụng `/bind` và `/send`.

---

## Nhật ký (JSONL)

- Mặc định: `log/messages.jsonl`. Bạn có thể thay đổi vị trí lưu trữ trong `.env` với `IMTBD_JSONL_PATH`.  
- Giao diện người dùng sẽ theo dõi tệp này và hiển thị trên màn hình. Có thể xem qua chia sẻ UNC.

---

## Ví dụ tích hợp với VS Code Wrapper

- Cấu hình phía mở rộng: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- Chọn → **Thay thế lựa chọn bằng tiếng Nhật** (ví dụ: `Ctrl+Alt+K`) để **thay thế ngay tại chỗ**

- Dịch clipboard (`Ctrl+Alt+J`), dịch khi di chuột, v.v. tuân theo cài đặt của phía mở rộng

---

## Câu hỏi thường gặp (FAQ)

**Q: Làm thế nào để viết đường dẫn UNC trên Windows?**  
A: Trong `.env`, bạn viết `\\raspberrypi\IMTB-D\messages.jsonl` với **hai dấu gạch chéo ngược**.  
   Do việc escape trong `.env`, thực tế nên viết là `\\\\raspberrypi\\IMTB-D\\messages.jsonl` cho an toàn.

**Q: Xuất hiện `fetch failed`**  
A: Có thể `localhost` đang giải quyết IPv6 và không thể kết nối. Hãy thử với **`127.0.0.1`**. Nếu là từ xa, hãy sử dụng `<server-ip>`.

**Q: Permission denied (ghi vào `console_routes.json`)**  
A: Có thể do trình soạn thảo đang mở tệp (độc quyền) hoặc do Controlled Folder Access của Windows. Thay đổi vị trí lưu trữ về thư mục người dùng hoặc đóng trình soạn thảo và chạy lại.

---

## Mẹo phát triển/vận hành

- **Hot reload cho r3** (khởi động lại khi lưu)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **Chạy nền (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Quản lý Git**
  
  - Cam kết thực hiện `/translate`, README, CHANGELOG
  
  - Không cam kết `.env` (cung cấp `.env.example`)
  
  - Nguyên tắc là bỏ qua `.vscode/`. Nếu muốn chia sẻ, chỉ chia sẻ những tệp tối thiểu không bí mật như `extensions.json`/`tasks.json`

---

## Giấy phép

Giấy phép MIT