# Interactive Multilingual Translator BOT for Discord(IMTB-D)

A tool that allows you to read and write Discord messages translated into your **preferred language** using a **Translation Relay Bot**, a **Desktop UI (Tkinter)** for local control, and a **Console** for terminal use. (As of 2025/09/08, supported languages: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th) Translation logs can be saved in **JSONL** format, and a UNC shared path (e.g., `\\raspberrypi\IMTB-D\messages.jsonl`) can also be specified.

- **Relay**: Discord Bot and local HTTP API (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI**: .env editing, destination registration and sending, log viewing, **file translation (live preview)**, automatic Relay startup when used locally.
- **Console**: Bind & send from the terminal. Tail display of logs.

> Requirements: **Discord Bot Token** and **OpenAI API Key**.

---

## Structure (Main Files)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Desktop UI (Tkinter)
IMTB-D_console.py    # Console for terminal
console_routes.json      # Destination storage (written by UI)
log/messages.jsonl       # Translation log (JSON Lines)
```

---

## Requirements

- Python 3.10+ (Environment where Tkinter can be used)
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

# It is recommended to use localhost when using locally (UI will automatically start Relay)
IMTBD_API_BASE=http://127.0.0.1:8765

# (Optional) Log storage location. Windows uses UNC, Linux/mac can use normal path
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Optional) Translation settings
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> When using UNC on Linux/mac, it is advisable to mount it in advance and specify it with a normal path. *Note that IMTBD_JSONL_PATH is **case-sensitive** (Linux)*

---

## How to Use

### A. Use UI + Relay Locally (Quickest)

```bash
python IMTB-D_ui.py
```

- If `IMTBD_API_BASE` is `http://127.0.0.1:8765` or `localhost`,  
  the UI will **automatically assist in starting Relay** (after startup, "API ready" will be displayed).
  
  ![setup.png](docs/images/setup.png)
  
  Edit the `.env` from the "Setup" tab and **Save .env**.

- In the "Destinations" tab, **Bind** the destination (DM/Channel) → enter text → **Send**.
  
  ![destinations.png](docs/images/destinations.png)

- The log at the bottom will reflect the sending and receiving.
  
  - Click "Open Window" while a destination (DM/Channel) is selected → an individual chat window will open.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Text Translation
    
    - Enter text in the box at the bottom of the window and press send or Enter to send.
    
    - If multiple lines are needed, you can insert a line break with Ctrl+Enter.
  
  - Image Translate (Inpaint)
    
    - Drag and drop an image to perform image translation using inpainting.
    
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

# To DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Typing directly into standard input will send the message (logs will be displayed in tail).
```

---

## API (Relay)

- `POST /bind` — Register console name and destination (dm/channel, id, lang)  
- `POST /send` — Send text to specified console (can temporarily overwrite with `lang`)  
- `POST /send_image` — Image OCR → translation → inpainting & drawing → sending  
- `GET  /stats` — Startup status and binding list

---

## Log (JSONL)

- Default: `log/messages.jsonl`. You can change the storage location with `IMTBD_JSONL_PATH` in `.env`.  
- The UI tails this file for display. It can also be viewed over UNC sharing.

---

## Frequently Asked Questions (FAQ)

**Q: How do I write a UNC path on Windows?**  
A: In `.env`, write `\\raspberrypi\IMTB-D\messages.jsonl` with **two backslashes**.  
   Due to escaping in `.env`, it is safer to write it as `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

---

## License

MIT License