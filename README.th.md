## Interactive Multilingual Translator BOT for Discord (IMTB-D)

Discord のメッセージを“好きな言語”に翻訳して読み書きできる **翻訳リレー Bot（Relay）**、それを手元から操作する **デスクトップ UI（Tkinter）**、ターミナルから使える **Console** をまとめたツールです。  
翻訳ログは **JSONL** で保存でき、UNC 共有パス（例: `\\raspberrypi\IMTB-D\messages.jsonl`）も指定可能。

- **Relay**: Discord Bot とローカル HTTP API（`/bind`, `/send`, `/send_image`, `/stats`）

- **Relay r3 追加**: **`/translate`**（HTTPでテキストを受け取り、**訳文をHTTPで返す汎用API**）

- **UI**: .env 編集、宛先の登録・送信、ログ閲覧、**ファイル翻訳（ライブプレビュー）**、ローカル時は Relay 自動起動

- **Console**: ターミナルからバインド＆送信。ログの tail 表示

> 必要なもの：**Discord Bot Token** と **OpenAI API Key**（OpenAI直叩きしない構成でもOK）

---

## 目次

- [構成](#%E6%A7%8B%E6%88%90)

- [要件](#%E8%A6%81%E4%BB%B6)

- [.env（最小例）](#env%E6%9C%80%E5%B0%8F%E4%BE%8B)

- [使い方](#%E4%BD%BF%E3%81%84%E6%96%B9)
  
  - [A. ローカルで UI + Relay](#a-%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E3%81%A7-ui--relay)
  
  - [B. リモート Relay に接続](#b-%E3%83%AA%E3%83%A2%E3%83%BC%E3%83%88-relay-%E3%81%AB%E6%8E%A5%E7%B6%9A)
  
  - [C. Console（ターミナル）](#c-console%E3%82%BF%E3%83%BC%E3%83%9F%E3%83%8A%E3%83%AB)

- [API（Relay）](#apirelay)
  
  - [/translate（r3 新規）](#translater3-%E6%96%B0%E8%A6%8F)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [ログ（JSONL）](#%E3%83%AD%E3%82%B0jsonl)

- [VS Code ラッパー連携例](#vs-code-%E3%83%A9%E3%83%83%E3%83%91%E3%83%BC%E9%80%A3%E6%90%BA%E4%BE%8B)

- [よくある質問](#%E3%82%88%E3%81%8F%E3%81%82%E3%82%8B%E8%B3%AA%E5%95%8F)

- [開発/運用Tips](#%E9%96%8B%E7%99%BA%E9%81%8B%E7%94%A8tips)

- [ライセンス](#%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9)

---

## 構成（主要ファイル）

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # デスクトップ UI（Tkinter）
IMTB-D_console.py    # ターミナル用コンソール
console_routes.json      # 宛先の保存（UIが書き込み）
log/messages.jsonl       # 翻訳ログ（JSON Lines）
```

---

## 要件

- 主要ファイルをダウンロード
- Python 3.10+（Tkinter が使える環境）
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env（最小例）

このリポジトリ直下に `.env` を作成します。

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Relay のベースURL（UIのローカル運用時は 127.0.0.1 を推奨）
IMTBD_API_BASE=http://127.0.0.1:8765

# Relay バインド（Listen）設定（未設定なら既定: 127.0.0.1:8765）
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# （任意）翻訳ログ保存先
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# （任意）翻訳関連
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Linux/mac で UNC を使うときは、事前にマウントして通常パスで指定するのが確実です。※IMTBD_JSONL_PATHは **大文字小文字を区別**（Linux）

---

## 使い方

### A. ローカルで UI + Relay を使う（最短）

```bash
python IMTB-D_ui.py
```

- `IMTBD_API_BASE` が `http://127.0.0.1:8765` または `localhost` の場合、  
  UI が **Relay の起動を自動で補助** します（起動後は「API ready」と表示）。
  
  ![setup.png](docs/images/setup.png)
  
  「Setup」タブから `.env` を編集して **Save .env**。

- 「Destinations」タブで宛先（DM/Channel）を **Bind** → テキスト入力 → **Send**。
  
  ![destinations.png](docs/images/destinations.png)

- 下部のログに送受が反映されます。
  
  - 宛先（DM/Channel）を 選択した状態で「Open Window」をクリック→個別チャット画面が開きます。
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - テキスト翻訳
    
    - ウィンドウ最下部のボックスにテキストを入力し、sendもしくはEnterを押すことで送信します。
    
    - 複数行の入力が必要な場合はCtrl+Enterで改行できます。
  
  - Image Translate(Inpaint)
    
    - 画像をD&Dすることでインペイント方式の画像翻訳を行います。
    
    - 現段階ではあまりきれいではないですが、参考程度にはなります。
      
      翻訳前
      
      ![origin.png](docs/images/origin.png)
      
      翻訳後
      
      ![translated.png](docs/images/translated.png)

### B. リモートの Relay（例: Raspberry Pi）に接続

- サーバ（Pi等）で `IMTB-D_relay.py` を起動しておき、
- UI 側の `.env` の `IMTBD_API_BASE` を `http://<server-ip>:8765` に設定。  
- この場合 UI の Start/Stop は無効化され、**リモートモード**として動作します。

### C. Console（ターミナル）

```bash
# チャンネルへ
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# DM へ
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# そのまま標準入力に打ち込むと送信されます（ログは tail 表示）。
```

---

## API（Relay）

### `/translate`（r3 新規）

**HTTPで受けたテキストを翻訳し、HTTPで訳文を返す汎用API**。Discordを経由しません。

- **POST** `/translate`

- **Request (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""`（未指定/auto/空は内部で自動判定）
  
  - `target`: 既定は `.env` の `DEFAULT_REPLY_LANG`（例: `"ja"`）

- **Response (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **例: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **例: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### 返り値の約束

- `ok` が `true` のとき `translated` に訳文

- 失敗時は `{ "ok": false, "error": "<message>" }` を返却（HTTP 4xx/5xx）

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — コンソール名と宛先（dm/channel, id, lang 等）を登録

- `POST /send` — 指定コンソールへテキスト送信（Discord 側へ配送）

- `POST /send_image` — 画像 OCR → 翻訳 → インペイント → 送信

- `GET /stats` — 起動状態・バインディング一覧> `/translate` เป็น **การตอบกลับโดยตรงไปยัง HTTP client** ทำให้เหมาะสำหรับการเชื่อมต่อกับเครื่องมือภายนอก เช่น VS Code ในขณะที่กระบวนการผ่าน Discord แบบเดิมใช้ `/bind` และ `/send` 

---

## บันทึก (JSONL)

- ค่าเริ่มต้น: `log/messages.jsonl` สามารถเปลี่ยนแปลงที่เก็บได้ใน `.env` โดยใช้ `IMTBD_JSONL_PATH`  
- UI จะ tail ไฟล์นี้และแสดงผลบนหน้าจอ สามารถเข้าถึงได้แม้ผ่าน UNC แชร์

---

## ตัวอย่างการเชื่อมต่อกับ VS Code Wrapper

- การตั้งค่าฝั่งส่วนขยาย: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- เลือก → **Replace Selection with Japanese** (ตัวอย่าง: `Ctrl+Alt+K`) เพื่อ **แทนที่ในที่นั้น**

- การแปลจากคลิปบอร์ด (`Ctrl+Alt+J`), การแปลแบบ hover เป็นต้น จะเป็นไปตามการตั้งค่าฝั่งส่วนขยาย

---

## คำถามที่พบบ่อย (FAQ)

**Q: UNC path ของ Windows เขียนอย่างไร?**  
A: ใน `.env` ให้เขียนเป็น `\\raspberrypi\IMTB-D\messages.jsonl` โดยใช้ **แบ็คสแลช 2 ตัว**  
   เนื่องจากการ escape ใน `.env` จริง ๆ แล้วควรเขียนเป็น `\\\\raspberrypi\\IMTB-D\\messages.jsonl` เพื่อความปลอดภัย

**Q: แสดง `fetch failed`**  
A: อาจเกิดจาก `localhost` แก้ไขเป็น IPv6 และไม่สามารถเชื่อมต่อได้ ลองใช้ **`127.0.0.1`** แทน หากเป็นการเชื่อมต่อระยะไกลให้ใช้ `<server-ip>`

**Q: Permission denied (การเขียน `console_routes.json`)**  
A: อาจเกิดจาก editor เปิดไฟล์อยู่ (การเข้าถึงแบบพิเศษ) หรือ Controlled Folder Access ของ Windows เป็นสาเหตุ ลองเปลี่ยนที่เก็บไปยังไดเรกทอรีผู้ใช้ หรือปิด editor และลองใหม่

---

## เคล็ดลับสำหรับการพัฒนา/การใช้งาน

- **การรีโหลดร้อนของ r3** (เริ่มใหม่เมื่อบันทึก)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **การทำให้ทำงานตลอด (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **การใช้งาน Git**
  
  - คอมมิตการดำเนินการ `/translate`, README, CHANGELOG
  
  - อย่าคอมมิต `.env` (ให้จัดเตรียม `.env.example`)
  
  - โดยหลักการให้ ignore `.vscode/` หากต้องการแชร์ให้แชร์เฉพาะ `extensions.json`/`tasks.json` เป็นต้น ที่ไม่มีข้อมูลลับ

---

## ไลเซนส์

MIT License