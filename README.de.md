## Interaktiver mehrsprachiger Übersetzer-BOT für Discord (IMTB-D)

Ein **Übersetzungs-Relay-Bot (Relay)**, der Discord-Nachrichten in eine „bevorzugte Sprache“ übersetzt und liest/schreibt, eine **Desktop-UI (Tkinter)** zur Steuerung von Ihrem Gerät aus und eine **Konsole**, die über das Terminal verwendet werden kann.  
Die Übersetzungsprotokolle können im **JSONL**-Format gespeichert werden, und ein UNC-Freigabepfad (z. B.: `\\raspberrypi\IMTB-D\messages.jsonl`) kann ebenfalls angegeben werden.

- **Relay**: Discord-Bot und lokale HTTP-API (`/bind`, `/send`, `/send_image`, `/stats`)

- **Zusatz Relay r3**: **`/translate`** (nimmt Text über HTTP entgegen und gibt **Übersetzungen über HTTP zurück**)

- **UI**: .env-Bearbeitung, Registrierung und Versand von Zielen, Protokollansicht, **Dateiübersetzung (Live-Vorschau)**, automatischer Start des Relays im lokalen Modus

- **Konsole**: Binden & Senden über das Terminal. Protokoll-Tail-Anzeige

> Benötigt: **Discord Bot Token** und **OpenAI API Key** (auch ohne direkte OpenAI-Anfragen möglich)

---

## Inhaltsverzeichnis

- [Konfiguration](#%E6%A7%8B%E6%88%90)

- [Anforderungen](#%E8%A6%81%E4%BB%B6)

- [.env (Minimalbeispiel)](#env%E6%9C%80%E5%B0%8F%E4%BE%8B)

- [Benutzung](#%E4%BD%BF%E3%81%84%E6%96%B9)
  
  - [A. Lokal mit UI + Relay](#a-%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E3%81%A7-ui--relay)
  
  - [B. Verbindung zu Remote Relay](#b-%E3%83%AA%E3%83%A2%E3%83%BC%E3%83%88-relay-%E3%81%AB%E6%8E%A5%E7%B6%9A)
  
  - [C. Konsole (Terminal)](#c-console%E3%82%BF%E3%83%BC%E3%83%9F%E3%83%8A%E3%83%AB)

- [API (Relay)](#apirelay)
  
  - [/translate (r3 neu)](#translater3-%E6%96%B0%E8%A6%8F)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [Protokoll (JSONL)](#%E3%83%AD%E3%82%B0jsonl)

- [Beispiel für VS Code Wrapper-Integration](#vs-code-%E3%83%A9%E3%83%83%E3%83%91%E3%83%BC%E9%80%A3%E6%90%BA%E4%BE%8B)

- [Häufig gestellte Fragen](#%E3%82%88%E3%81%8F%E3%81%82%E3%82%8B%E8%B3%AA%E5%95%8F)

- [Entwicklungs-/Betriebstipps](#%E9%96%8B%E7%99%BA%E9%81%8B%E7%94%A8tips)

- [Lizenz](#%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9)

---

## Konfiguration (Hauptdateien)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Desktop UI (Tkinter)
IMTB-D_console.py    # Konsole für das Terminal
console_routes.json      # Speicherung der Ziele (UI schreibt)
log/messages.jsonl       # Übersetzungsprotokoll (JSON Lines)
```

---

## Anforderungen

- Hauptdateien herunterladen
- Python 3.10+ (Umgebung, in der Tkinter verwendet werden kann)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (Minimalbeispiel)

Erstellen Sie eine `.env`-Datei im Stammverzeichnis dieses Repositories.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Basis-URL für Relay (empfohlen: 127.0.0.1 für lokale Nutzung der UI)
IMTBD_API_BASE=http://127.0.0.1:8765

# Relay-Bindung (Listen) Einstellungen (Standard: 127.0.0.1:8765, wenn nicht konfiguriert)
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# (Optional) Speicherort für Übersetzungsprotokolle
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Optional) Übersetzungsbezogene Einstellungen
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Wenn Sie UNC unter Linux/mac verwenden, ist es sicherer, es vorher zu mounten und den normalen Pfad anzugeben. ※IMTBD_JSONL_PATH ist **groß- und kleinschreibungsempfindlich** (Linux)

---

## Benutzung

### A. Lokal mit UI + Relay verwenden (schnellste Methode)

```bash
python IMTB-D_ui.py
```

- Wenn `IMTBD_API_BASE` auf `http://127.0.0.1:8765` oder `localhost` gesetzt ist,  
  unterstützt die UI **automatisch den Start des Relays** (nach dem Start wird „API bereit“ angezeigt).
  
  ![setup.png](docs/images/setup.png)
  
  Bearbeiten Sie die `.env`-Datei über den „Setup“-Tab und **Speichern Sie .env**.

- Im „Destinations“-Tab Ziel (DM/Channel) **Binden** → Texteingabe → **Senden**.
  
  ![destinations.png](docs/images/destinations.png)

- Die gesendeten und empfangenen Nachrichten werden im unteren Protokoll angezeigt.
  
  - Klicken Sie auf „Open Window“, während das Ziel (DM/Channel) ausgewählt ist → das individuelle Chatfenster öffnet sich.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Textübersetzung
    
    - Geben Sie den Text in das unterste Feld des Fensters ein und drücken Sie Senden oder Enter, um zu senden.
    
    - Wenn mehrere Zeilen eingegeben werden müssen, können Sie mit Ctrl+Enter einen Zeilenumbruch machen.
  
  - Bildübersetzung (Inpaint)
    
    - Ziehen Sie ein Bild per Drag & Drop, um eine bildbasierte Übersetzung durchzuführen.
    
    - Derzeit ist die Qualität nicht sehr hoch, aber es kann als Referenz dienen.
      
      Vor der Übersetzung
      
      ![origin.png](docs/images/origin.png)
      
      Nach der Übersetzung
      
      ![translated.png](docs/images/translated.png)

### B. Verbindung zu Remote Relay (z. B. Raspberry Pi)

- Starten Sie `IMTB-D_relay.py` auf dem Server (Pi usw.),
- Stellen Sie die `IMTBD_API_BASE` in der `.env`-Datei der UI auf `http://<server-ip>:8765` ein.  
- In diesem Fall sind die Start-/Stopp-Funktionen der UI deaktiviert und es funktioniert im **Remote-Modus**.

### C. Konsole (Terminal)

```bash
# Zu einem Kanal
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Zu einer DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Geben Sie einfach in die Standard-Eingabe ein, um zu senden (Protokoll wird im Tail angezeigt).
```

---

## API (Relay)

### `/translate` (r3 neu)

**Übersetzt den über HTTP empfangenen Text und gibt die Übersetzung über HTTP zurück**. Geht nicht über Discord.

- **POST** `/translate`

- **Anfrage (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""` (nicht angegeben/auto/leere wird intern automatisch erkannt)
  
  - `target`: Standardmäßig `.env`-Einstellung `DEFAULT_REPLY_LANG` (z. B.: `"ja"`)

- **Antwort (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **Beispiel: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **Beispiel: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### Rückgabewerte

- Wenn `ok` `true` ist, enthält `translated` die Übersetzung

- Bei Fehlern wird `{ "ok": false, "error": "<message>" }` zurückgegeben (HTTP 4xx/5xx)

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — Registriert den Konsolennamen und das Ziel (dm/channel, id, lang usw.)

- `POST /send` — Sendet Text an die angegebene Konsole (wird an Discord geliefert)

- `POST /send_image` — Bild-OCR → Übersetzung → Inpainting → Senden

- `GET /stats` — Startstatus und Bindungsübersicht> `/translate` ist **optimal, um direkt auf HTTP-Clients zu antworten**, ideal für externe Tool-Integrationen wie VS Code. Der traditionelle Discord-Workflow verwendet `/bind` und `/send`.

---

## Log (JSONL)

- Standard: `log/messages.jsonl`. Der Speicherort kann in `.env` unter `IMTBD_JSONL_PATH` geändert werden.  
- Die UI überwacht diese Datei und zeigt sie an. Sie ist auch über UNC-Freigaben zugänglich.

---

## Beispiel für VS Code Wrapper-Integration

- Erweiterungseinstellungen: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- Auswahl → **Auswahl mit Japanisch ersetzen** (z. B.: `Ctrl+Alt+K`) für **Ersatz vor Ort**

- Zwischenablage-Übersetzung (`Ctrl+Alt+J`), Hover-Übersetzung usw. richten sich nach den Einstellungen der Erweiterung

---

## Häufig gestellte Fragen (FAQ)

**F: Wie schreibe ich den UNC-Pfad unter Windows?**  
A: In `.env` wird `\\raspberrypi\IMTB-D\messages.jsonl` mit **zwei Rückwärtsschlägen** angegeben.  
   Aufgrund der Escape-Sequenzen in `.env` ist es ratsam, tatsächlich `\\\\raspberrypi\\IMTB-D\\messages.jsonl` zu schreiben.

**F: `fetch failed` erscheint**  
A: Es kann sein, dass `localhost` nicht über IPv6 aufgelöst werden kann. Bitte versuchen Sie es mit **`127.0.0.1`**. Verwenden Sie im Remote-Fall `<server-ip>`.

**F: Permission denied (Schreiben in `console_routes.json`)**  
A: Möglicherweise hat der Editor die Datei geöffnet (exklusiv) oder es liegt an der Controlled Folder Access-Funktion von Windows. Ändern Sie den Speicherort in das Benutzerverzeichnis oder schließen Sie den Editor und führen Sie es erneut aus.

---

## Entwicklungs-/Betriebstipps

- **Hot Reload für r3** (Neustart bei Speicherung)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **Dauerbetrieb (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Git-Nutzung**
  
  - `/translate` Implementierung, README, CHANGELOG committen
  
  - `.env` nicht committen (stattdessen `.env.example` bereitstellen)
  
  - `.vscode/` grundsätzlich ignorieren. Wenn geteilt werden soll, nur die minimalen, nicht vertraulichen Dateien wie `extensions.json`/`tasks.json`

---

## Lizenz

MIT-Lizenz