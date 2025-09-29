## Interactive Multilingual Translator BOT for Discord (IMTB-D)

A tool that combines a **Translation Relay Bot** for translating Discord messages into your "preferred language," a **Desktop UI (Tkinter)** for local control, and a **Console** for terminal usage.  
Translation logs can be saved in **JSONL** format, and a UNC share path (e.g., `\\raspberrypi\IMTB-D\messages.jsonl`) can also be specified.

- **Relay**: Discord Bot and local HTTP API (`/bind`, `/send`, `/send_image`, `/stats`)

- **Relay r3 addition**: **`/translate`** (a general API that receives text via HTTP and returns the **translated text via HTTP**)

- **UI**: Edit .env, register/send destinations, view logs, **file translation (live preview)**, automatic Relay startup when local

- **Console**: Bind & send from the terminal. Tail display of logs

> Requirements: **Discord Bot Token** and **OpenAI API Key** (configuration without direct OpenAI calls is also acceptable)

---

## Table of Contents

- [Configuration](#configuration)

- [Requirements](#requirements)

- [.env (Minimal Example)](#env-minimal-example)

- [Usage](#usage)
  
  - [A. Local UI + Relay](#a-local-ui--relay)
  
  - [B. Connect to Remote Relay](#b-connect-to-remote-relay)
  
  - [C. Console (Terminal)](#c-console-terminal)

- [API (Relay)](#api-relay)
  
  - [/translate (r3 New)](#translate-r3-new)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [Logs (JSONL)](#logs-jsonl)

- [VS Code Wrapper Integration Example](#vs-code-wrapper-integration-example)

- [Frequently Asked Questions](#frequently-asked-questions)

- [Development/Operation Tips](#developmentoperation-tips)

- [License](#license)

---

## Configuration (Main Files)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Desktop UI (Tkinter)
IMTB-D_console.py    # Console for terminal
console_routes.json      # Save destinations (written by UI)
log/messages.jsonl       # Translation logs (JSON Lines)
```

---

## Requirements

- Download the main files
- Python 3.10+ (environment where Tkinter is available)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (Minimal Example)

Create a `.env` file at the root of this repository.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Base URL for Relay (recommended 127.0.0.1 when running UI locally)
IMTBD_API_BASE=http://127.0.0.1:8765

# Relay bind (Listen) settings (default: 127.0.0.1:8765 if not set)
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# (Optional) Translation log save location
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Optional) Translation related
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> When using UNC on Linux/mac, it is advisable to mount it in advance and specify it with a normal path. Note that IMTBD_JSONL_PATH is **case-sensitive** (Linux).

---

## Usage

### A. Local UI + Relay (Quickest)

```bash
python IMTB-D_ui.py
```

- If `IMTBD_API_BASE` is `http://127.0.0.1:8765` or `localhost`,  
  the UI will **automatically assist in starting the Relay** (after startup, it will display "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Edit the `.env` from the "Setup" tab and **Save .env**.

- In the "Destinations" tab, **Bind** the destination (DM/Channel) → enter text → **Send**.
  
  ![destinations.png](docs/images/destinations.png)

- The log at the bottom will reflect the sent and received messages.
  
  - Click "Open Window" while selecting a destination (DM/Channel) → an individual chat window will open.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Text Translation
    
    - Enter text in the box at the bottom of the window and press send or Enter to send.
    
    - For multiple lines, you can press Ctrl+Enter to create a new line.
  
  - Image Translate (Inpaint)
    
    - Drag and drop an image to perform inpainting image translation.
    
    - Currently, the results may not be very clean, but they can serve as a reference.
      
      Before Translation
      
      ![origin.png](docs/images/origin.png)
      
      After Translation
      
      ![translated.png](docs/images/translated.png)

### B. Connect to Remote Relay (e.g., Raspberry Pi)

- Start `IMTB-D_relay.py` on the server (e.g., Pi),
- Set `IMTBD_API_BASE` in the UI's `.env` to `http://<server-ip>:8765`.  
- In this case, the Start/Stop in the UI will be disabled, and it will operate in **remote mode**.

### C. Console (Terminal)

```bash
# To a channel
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# To a DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Typing directly into standard input will send the message (logs will be displayed in tail).
```

---

## API (Relay)

### `/translate` (r3 New)

**A general API that translates text received via HTTP and returns the translated text via HTTP**. It does not go through Discord.

- **POST** `/translate`

- **Request (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""` (unspecified/auto/empty will be automatically determined internally)
  
  - `target`: defaults to `.env`'s `DEFAULT_REPLY_LANG` (e.g., `"ja"`)

- **Response (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **Example: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **Example: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### Return Value Guarantees

- When `ok` is `true`, `translated` will contain the translated text.

- On failure, it will return `{ "ok": false, "error": "<message>" }` (HTTP 4xx/5xx)

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — Register console name and destination (dm/channel, id, lang, etc.)

- `POST /send` — Send text to the specified console (delivered to Discord)

- `POST /send_image` — Image OCR → translation → inpainting → sending

- `GET /stats` — Startup status and binding list> `/translate` is optimal for **direct replies to HTTP clients**, making it suitable for integrations with external tools like VS Code. The traditional Discord flow uses `/bind` and `/send`.

---

## Logs (JSONL)

- Default: `log/messages.jsonl`. You can change the save location with `IMTBD_JSONL_PATH` in `.env`.  
- The UI tails this file for display. It can be accessed even over UNC shares.

---

## VS Code Wrapper Integration Example

- Extension configuration: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- Select → **Replace Selection with Japanese** (e.g., `Ctrl+Alt+K`) for **in-place replacement**

- Clipboard translation (`Ctrl+Alt+J`), hover translation, etc., follow the extension's settings

---

## Frequently Asked Questions (FAQ)

**Q: How do I write a UNC path in Windows?**  
A: In `.env`, write `\\raspberrypi\IMTB-D\messages.jsonl` with **two backslashes**.  
   Due to escaping in `.env`, it's safer to write it as `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

**Q: `fetch failed` appears**  
A: `localhost` may be resolving to IPv6, causing connection issues. Please try **`127.0.0.1`**. Use `<server-ip>` for remote connections.

**Q: Permission denied (writing `console_routes.json`)**  
A: This may occur if the editor has the file open (exclusive access) or due to Windows Controlled Folder Access. Change the save location to the user directory or close the editor and try again.

---

## Development/Operational Tips

- **Hot Reload for r3** (restarts on save)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **Daemonization (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Git Operations**
  
  - Commit the implementation of `/translate`, README, and CHANGELOG
  
  - Do not commit `.env` (provide `.env.example`)
  
  - Generally ignore `.vscode/`. If sharing, only include the minimum necessary without secrets, such as `extensions.json`/`tasks.json`, etc.

---

## License

MIT License