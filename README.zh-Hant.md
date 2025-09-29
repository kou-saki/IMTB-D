## 互動式多語言翻譯機器人 BOT for Discord (IMTB-D)

這是一個可以將 Discord 的訊息翻譯成“喜歡的語言”的 **翻譯中繼 Bot（Relay）**，並且可以通過 **桌面 UI（Tkinter）** 和終端使用的 **Console** 的綜合工具。  
翻譯日誌可以以 **JSONL** 格式保存，並且可以指定 UNC 共享路徑（例如: `\\raspberrypi\IMTB-D\messages.jsonl`）。

- **Relay**: Discord Bot 和本地 HTTP API（`/bind`, `/send`, `/send_image`, `/stats`）

- **Relay r3 追加**: **`/translate`**（接收文本並通過 HTTP 返回翻譯的通用 API）

- **UI**: 編輯 .env，註冊和發送目的地，查看日誌，**文件翻譯（即時預覽）**，在本地時自動啟動 Relay

- **Console**: 從終端綁定和發送。日誌的 tail 顯示

> 需要的東西：**Discord Bot Token** 和 **OpenAI API Key**（不直接調用 OpenAI 的配置也可以）

---

## 目錄

- [構成](#%E6%A7%8B%E6%88%90)

- [要件](#%E8%A6%81%E4%BB%B6)

- [.env（最小例）](#env%E6%9C%80%E5%B0%8F%E4%BE%8B)

- [使用方法](#%E4%BD%BF%E7%94%A8%E6%96%B9)
  
  - [A. 本地使用 UI + Relay](#a-%E6%9C%AC%E5%9C%B0%E4%BD%BF%E7%94%A8-ui--relay)
  
  - [B. 連接到遠程 Relay](#b-%E9%80%A3%E6%8E%A5%E5%88%B0%E9%81%A0%E9%9C%8D-relay)
  
  - [C. Console（終端）](#c-console%E7%B5%82%E7%AB%AF)

- [API（Relay）](#apirelay)
  
  - [/translate（r3 新規）](#translater3-%E6%96%B0%E8%A6%8F)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [日誌（JSONL）](#%E6%97%A5%E8%AA%8Cjsonl)

- [VS Code 包裝器整合範例](#vs-code-%E5%8C%85%E8%A3%9D%E5%99%A8%E6%95%B4%E5%90%88%E7%AF%84%E4%BE%8B)

- [常見問題](#%E5%B8%B8%E8%A6%8B%E5%95%8F%E9%A1%8C)

- [開發/運行小技巧](#%E9%96%8B%E7%99%BC%E9%81%8B%E8%A1%8C%E5%B0%8F%E5%B7%A7)

- [授權](#%E6%8E%88%E6%AC%8A)

---

## 構成（主要文件）

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # 桌面 UI（Tkinter）
IMTB-D_console.py    # 終端用控制台
console_routes.json      # 保存目的地（UI 寫入）
log/messages.jsonl       # 翻譯日誌（JSON Lines）
```

---

## 要件

- 下載主要文件
- Python 3.10+（可使用 Tkinter 的環境）
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env（最小例）

在此倉庫的根目錄下創建 `.env`。

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Relay 的基礎 URL（在 UI 本地運行時建議使用 127.0.0.1）
IMTBD_API_BASE=http://127.0.0.1:8765

# Relay 綁定（監聽）設置（未設置則默認: 127.0.0.1:8765）
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# （可選）翻譯日誌保存位置
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# （可選）翻譯相關
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> 在 Linux/mac 使用 UNC 時，事先掛載並以常規路徑指定是最可靠的。※IMTBD_JSONL_PATH 是 **區分大小寫**（Linux）

---

## 使用方法

### A. 本地使用 UI + Relay（最短）

```bash
python IMTB-D_ui.py
```

- 當 `IMTBD_API_BASE` 為 `http://127.0.0.1:8765` 或 `localhost` 時，  
  UI 將 **自動協助啟動 Relay**（啟動後顯示「API ready」）。
  
  ![setup.png](docs/images/setup.png)
  
  在「Setup」標籤中編輯 `.env` 並 **保存 .env**。

- 在「Destinations」標籤中選擇目的地（DM/Channel）並 **綁定** → 輸入文本 → **發送**。
  
  ![destinations.png](docs/images/destinations.png)

- 下方的日誌將反映發送和接收的內容。
  
  - 在選擇目的地（DM/Channel）的狀態下，點擊「Open Window」→將打開個別聊天畫面。
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - 文本翻譯
    
    - 在窗口最下方的框中輸入文本，按 send 或 Enter 鍵發送。
    
    - 如果需要多行輸入，可以使用 Ctrl+Enter 進行換行。
  
  - 圖片翻譯（Inpaint）
    
    - 通過拖放圖片進行 Inpaint 方式的圖片翻譯。
    
    - 目前階段效果不太理想，但可以作為參考。
      
      翻譯前
      
      ![origin.png](docs/images/origin.png)
      
      翻譯後
      
      ![translated.png](docs/images/translated.png)

### B. 連接到遠程 Relay（例如：Raspberry Pi）

- 在伺服器（如 Pi）上啟動 `IMTB-D_relay.py`，
- 在 UI 端的 `.env` 中將 `IMTBD_API_BASE` 設置為 `http://<server-ip>:8765`。  
- 在這種情況下，UI 的啟動/停止將被禁用，並作為 **遠程模式** 運行。

### C. Console（終端）

```bash
# 發送到頻道
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# 發送到 DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# 直接在標準輸入中輸入將會發送（日誌顯示為 tail）。
```

---

## API（Relay）

### `/translate`（r3 新規）

**接收 HTTP 的文本進行翻譯，並通過 HTTP 返回翻譯的通用 API**。不經過 Discord。

- **POST** `/translate`

- **請求 (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""`（未指定/auto/空為內部自動判定）
  
  - `target`: 默認為 `.env` 中的 `DEFAULT_REPLY_LANG`（例如: `"ja"`）

- **響應 (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **範例: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **範例: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### 返回值的約定

- 當 `ok` 為 `true` 時，`translated` 中包含翻譯文本

- 失敗時返回 `{ "ok": false, "error": "<message>" }`（HTTP 4xx/5xx）

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — 註冊控制台名稱和目的地（dm/channel, id, lang 等）

- `POST /send` — 向指定控制台發送文本（發送到 Discord 端）

- `POST /send_image` — 圖片 OCR → 翻譯 → Inpaint → 發送

- `GET /stats` — 啟動狀態和綁定列表> `/translate` 是 **直接回覆 HTTP 客戶端** 的最佳選擇，適合與 VS Code 等外部工具整合。傳統的 Discord 流程則使用 `/bind` 和 `/send`。

---

## 日誌（JSONL）

- 預設: `log/messages.jsonl`。可以在 `.env` 的 `IMTBD_JSONL_PATH` 中更改儲存位置。  
- UI 將持續監控此檔案並顯示在畫面上。即使透過 UNC 共享也可以查看。

---

## VS Code 包裝器整合範例

- 擴展側設定：`mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- 選擇 → **用日文替換選擇內容**（例如: `Ctrl+Alt+K`）進行**即時替換**

- クリップボード翻譯（`Ctrl+Alt+J`）、懸停翻譯等遵循擴展側的設定

---

## 常見問題（FAQ）

**Q: Windows 的 UNC 路徑該如何書寫？**  
A: 在 `.env` 中應該使用 **兩個反斜線** 來描述 `\\raspberrypi\IMTB-D\messages.jsonl`。  
   由於 `.env` 中的轉義，實際上建議寫成 `\\\\raspberrypi\\IMTB-D\\messages.jsonl`。

**Q: 出現 `fetch failed`**  
A: 可能是 `localhost` 的 IPv6 解析導致無法連接。請嘗試使用 **`127.0.0.1`**。如果是遠端，請使用 `<server-ip>`。

**Q: Permission denied（`console_routes.json` 寫入）**  
A: 可能是編輯器仍然開啟該檔案（排他）或 Windows 的受控資料夾存取造成的。請更改儲存位置至使用者目錄，或關閉編輯器後重新執行。

---

## 開發/運行提示

- **r3 的熱重載**（保存時自動重啟）
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **常駐化（Linux, systemd）**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Git 運用**
  
  - 提交 `/translate` 實作、README 和 CHANGELOG
  
  - 不要提交 `.env`（提供 `.env.example`）
  
  - 原則上忽略 `.vscode/`。如果需要共享，僅限於 `extensions.json`/`tasks.json` 等不含機密的最小部分

---

## 授權

MIT 授權