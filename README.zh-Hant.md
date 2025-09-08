# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Discord 的消息可以翻譯成 “喜歡的語言” 進行讀寫的 **翻譯中繼 Bot（Relay）**，  
以及可以從手邊操作的 **桌面 UI（Tkinter）**，還有可以從終端使用的 **Console**，這是一個綜合工具。(截至2025/09/08的支援語言：en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th)  
翻譯日誌可以以 **JSONL** 格式保存，並且可以指定 UNC 共享路徑（例如： `\\raspberrypi\IMTB-D\messages.jsonl`）。

- **Relay**: Discord Bot 和本地 HTTP API（`/bind`, `/send`, `/send_image`, `/stats`）。
- **UI**: .env 編輯、目的地的註冊與發送、日誌查看、**文件翻譯（即時預覽）**、本地時自動啟動 Relay。
- **Console**: 從終端進行綁定與發送。日誌的 tail 顯示。

> 需要的東西：**Discord Bot Token** 和 **OpenAI API Key**。

---

## 結構（主要文件）

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # 桌面 UI（Tkinter）
IMTB-D_console.py    # 終端用控制台
console_routes.json      # 目的地的保存（UI寫入）
log/messages.jsonl       # 翻譯日誌（JSON Lines）
```

---

## 要件

- Python 3.10+（可使用 Tkinter 的環境）
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env（最小範例）

在此倉庫根目錄下創建 `.env`。

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# 本地使用時建議使用 localhost（UI 自動啟動 Relay）
IMTBD_API_BASE=http://127.0.0.1:8765

# （可選）日誌的保存位置。Windows 使用 UNC，Linux/mac 使用常規路徑即可
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# （可選）翻譯設置
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> 在 Linux/mac 使用 UNC 時，建議事先掛載並使用常規路徑指定。※IMTBD_JSONL_PATH 是 **區分大小寫**（Linux）。

---

## 使用方法

### A. 本地使用 UI + Relay（最簡單）

```bash
python IMTB-D_ui.py
```

- 當 `IMTBD_API_BASE` 為 `http://127.0.0.1:8765` 或 `localhost` 時，  
  UI 將 **自動輔助啟動 Relay**（啟動後顯示「API ready」）。
  
  ![setup.png](docs/images/setup.png)
  
  在「Setup」標籤中編輯 `.env` 並 **保存 .env**。

- 在「Destinations」標籤中綁定目的地（DM/Channel）→ 輸入文本 → **發送**。
  
  ![destinations.png](docs/images/destinations.png)

- 下方的日誌將反映發送與接收的內容。
  
  - 在選擇目的地（DM/Channel）的狀態下，點擊「Open Window」→ 將打開個別聊天畫面。
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - 文本翻譯
    
    - 在窗口最下方的框中輸入文本，按 send 或 Enter 鍵發送。
    
    - 若需要輸入多行，可以使用 Ctrl+Enter 進行換行。
  
  - 圖像翻譯（Inpaint）
    
    - 通過拖放圖片進行圖像翻譯，使用的是修補方式。
    
    - 目前效果不是很好，但可以作為參考。
      
      翻譯前
      
      ![origin.png](docs/images/origin.png)
      
      翻譯後
      
      ![translated.png](docs/images/translated.png)

### B. 連接到遠程的 Relay（例如：Raspberry Pi）

- 在伺服器（如 Pi）上啟動 `IMTB-D_relay.py`，  
- 在 UI 端的 `.env` 中將 `IMTBD_API_BASE` 設定為 `http://<server-ip>:8765`。  
- 在這種情況下，UI 的 Start/Stop 將無效，並作為 **遠程模式** 運行。

### C. Console（終端）

```bash
# 發送到頻道
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# 發送到 DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# 直接在標準輸入中輸入將被發送（日誌將以 tail 顯示）。
```

---

## API（Relay）

- `POST /bind` — 註冊控制台名稱和目的地（dm/channel, id, lang）  
- `POST /send` — 向指定控制台發送文本（`lang` 可臨時覆蓋）  
- `POST /send_image` — 圖像的 OCR → 翻譯 → 修補與繪製 → 發送  
- `GET  /stats` — 啟動狀態與綁定列表

---

## 日誌（JSONL）

- 預設：`log/messages.jsonl`。可以通過 `.env` 的 `IMTBD_JSONL_PATH` 更改保存位置。  
- UI 將 tail 此文件並顯示在畫面上。即使通過 UNC 共享也可以查看。

---

## 常見問題（FAQ）

**Q: Windows 的 UNC 路徑該如何寫？**  
A: 在 `.env` 中應該寫作 `\\raspberrypi\IMTB-D\messages.jsonl`，使用 **兩個反斜杠**。  
   由於 `.env` 中的轉義，實際上寫作 `\\\\raspberrypi\\IMTB-D\\messages.jsonl` 是比較安全的。

---

## 授權

MIT 授權