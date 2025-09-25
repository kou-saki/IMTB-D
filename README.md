# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Discord のメッセージを “好きな言語” に翻訳して読み書きできる **翻訳リレー Bot（Relay）**、
それを手元から操作する **デスクトップ UI（Tkinter）**、ターミナルから使える **Console** をまとめたツールです。(2025/09/08現在の対応：en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th)
翻訳ログは **JSONL** で保存でき、UNC 共有パス（例: `\\raspberrypi\IMTB-D\messages.jsonl`）も指定可能。

- **Relay**: Discord Bot とローカル HTTP API（`/bind`, `/send`, `/send_image`, `/stats`）。
- **UI**: .env 編集、宛先の登録・送信、ログ閲覧、**ファイル翻訳（ライブプレビュー）**、ローカル時は Relay 自動起動。
- **Console**: ターミナルからバインド＆送信。ログの tail 表示。

> 必要なもの：**Discord Bot Token** と **OpenAI API Key**。

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

# ローカルで使う場合は localhost を推奨（UIが Relay を自動起動）
IMTBD_API_BASE=http://127.0.0.1:8765

# （任意）ログの保存先。WindowsはUNC, Linux/macは通常パスでOK
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# （任意）翻訳設定
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

- `POST /bind` — コンソール名と宛先（dm/channel, id, lang）を登録  
- `POST /send` — 指定コンソールへテキスト送信（`lang` で一時上書き可）  
- `POST /send_image` — 画像の OCR → 翻訳 → インペイント＆描画 → 送信  
- `GET  /stats` — 起動状態・バインディング一覧

---

## ログ（JSONL）

- 既定: `log/messages.jsonl`。`.env` の `IMTBD_JSONL_PATH` で保存先を変更できます。  
- UI はこのファイルを tail して画面表示します。UNC 共有越しでも閲覧可能です。

---

## よくある質問（FAQ）

**Q: Windows の UNC パスはどう書く？**  
A: `.env` では `\\raspberrypi\IMTB-D\messages.jsonl` を **バックスラッシュ2本**で記述します。  
   `.env` 内のエスケープ上、実際は `\\\\raspberrypi\\IMTB-D\\messages.jsonl` と書くのが無難です。

---

## ライセンス

MITライセンス
