# Interaktiver mehrsprachiger Übersetzer-BOT für Discord (IMTB-D)

Ein **Übersetzungs-Relay-Bot (Relay)**, der Discord-Nachrichten in eine “bevorzugte Sprache” übersetzen und lesen sowie schreiben kann, zusammen mit einer **Desktop-UI (Tkinter)** zur Steuerung und einer **Konsole**, die über das Terminal verwendet werden kann. (Stand 2025/09/08: Unterstützung für: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th) Übersetzungsprotokolle können im **JSONL**-Format gespeichert werden, und ein UNC-Freigabepfad (z. B.: `\\raspberrypi\IMTB-D\messages.jsonl`) kann ebenfalls angegeben werden.

- **Relay**: Discord Bot und lokale HTTP-API (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI**: .env-Bearbeitung, Registrierung und Versand von Zielen, Protokollansicht, **Dateiübersetzung (Live-Vorschau)**, automatische Relay-Start bei lokalem Betrieb.
- **Console**: Binden und Senden über das Terminal. Anzeige von Protokollen im Tail-Modus.

> Benötigt: **Discord Bot Token** und **OpenAI API Key**.

---

## Struktur (Hauptdateien)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Desktop UI (Tkinter)
IMTB-D_console.py    # Konsole für das Terminal
console_routes.json      # Speicherung der Ziele (UI schreibt)
log/messages.jsonl       # Übersetzungsprotokoll (JSON Lines)
```

---

## Anforderungen

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

# Für die lokale Nutzung wird localhost empfohlen (UI startet Relay automatisch)
IMTBD_API_BASE=http://127.0.0.1:8765

# (Optional) Speicherort für Protokolle. Windows verwendet UNC, Linux/mac kann den normalen Pfad verwenden
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Optional) Übersetzungseinstellungen
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Wenn Sie UNC unter Linux/mac verwenden, ist es sicherer, es vorher zu mounten und den normalen Pfad anzugeben. ※IMTBD_JSONL_PATH ist **groß- und kleinschreibungsempfindlich** (Linux)

---

## Verwendung

### A. Lokale Nutzung von UI + Relay (schnellste Methode)

```bash
python IMTB-D_ui.py
```

- Wenn `IMTBD_API_BASE` auf `http://127.0.0.1:8765` oder `localhost` gesetzt ist,  
  unterstützt die UI **automatisch den Start von Relay** (nach dem Start wird „API ready“ angezeigt).
  
  ![setup.png](docs/images/setup.png)
  
  Bearbeiten Sie die `.env`-Datei im Tab „Setup“ und klicken Sie auf **Save .env**.

- Im Tab „Destinations“ Ziel (DM/Channel) **Binden** → Texteingabe → **Senden**.
  
  ![destinations.png](docs/images/destinations.png)

- Die gesendeten und empfangenen Nachrichten werden im Protokoll unten angezeigt.
  
  - Wählen Sie das Ziel (DM/Channel) aus und klicken Sie auf „Open Window“ → ein individuelles Chatfenster öffnet sich.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Textübersetzung
    
    - Geben Sie den Text in das untere Feld des Fensters ein und drücken Sie Senden oder Enter, um ihn zu senden.
    
    - Für die Eingabe mehrerer Zeilen können Sie Ctrl+Enter verwenden, um einen Zeilenumbruch zu erzeugen.
  
  - Bildübersetzung (Inpaint)
    
    - Ziehen Sie ein Bild per Drag & Drop, um eine Bildübersetzung im Inpaint-Verfahren durchzuführen.
    
    - Derzeit ist die Qualität nicht sehr hoch, aber es kann als Referenz dienen.
      
      Vor der Übersetzung
      
      ![origin.png](docs/images/origin.png)
      
      Nach der Übersetzung
      
      ![translated.png](docs/images/translated.png)

### B. Verbindung zu einem Remote-Relay (z. B. Raspberry Pi)

- Starten Sie `IMTB-D_relay.py` auf dem Server (z. B. Pi),
- Stellen Sie `IMTBD_API_BASE` in der `.env`-Datei der UI auf `http://<server-ip>:8765` ein.  
- In diesem Fall sind die Start-/Stopp-Funktionen der UI deaktiviert und es funktioniert im **Remote-Modus**.

### C. Konsole (Terminal)

```bash
# Zu einem Kanal
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Zu einer DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Geben Sie einfach in die Standard-Eingabe ein, um zu senden (Protokoll wird im Tail-Modus angezeigt).
```

---

## API (Relay)

- `POST /bind` — Registriert den Konsolennamen und das Ziel (dm/channel, id, lang)  
- `POST /send` — Sendet Text an die angegebene Konsole (kann temporär mit `lang` überschrieben werden)  
- `POST /send_image` — OCR des Bildes → Übersetzung → Inpaint & Zeichnen → Senden  
- `GET  /stats` — Startzustand und Bindungsübersicht

---

## Protokoll (JSONL)

- Standard: `log/messages.jsonl`. Der Speicherort kann über `IMTBD_JSONL_PATH` in der `.env`-Datei geändert werden.  
- Die UI zeigt diese Datei im Tail-Modus an. Auch über UNC-Freigaben zugänglich.

---

## Häufig gestellte Fragen (FAQ)

**Q: Wie schreibe ich einen UNC-Pfad unter Windows?**  
A: In der `.env`-Datei wird `\\raspberrypi\IMTB-D\messages.jsonl` mit **zwei Rückwärtsschrägstrichen** geschrieben.  
   Aufgrund der Escape-Sequenzen in der `.env`-Datei ist es sicherer, tatsächlich `\\\\raspberrypi\\IMTB-D\\messages.jsonl` zu schreiben.

---

## Lizenz

MIT-Lizenz