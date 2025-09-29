## Interactive Multilingual Translator BOT for Discord (IMTB-D)

Alat ini adalah **翻訳リレー Bot（Relay）** yang dapat menerjemahkan pesan Discord ke dalam “bahasa yang diinginkan”, serta **UI Desktop (Tkinter)** untuk mengoperasikannya dari tangan Anda, dan **Console** yang dapat digunakan dari terminal.  
Log terjemahan dapat disimpan dalam **JSONL** dan juga dapat menentukan jalur berbagi UNC (contoh: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Discord Bot dan API HTTP lokal (`/bind`, `/send`, `/send_image`, `/stats`)

- **Relay r3 tambahan**: **`/translate`** (API umum yang menerima teks melalui HTTP dan mengembalikan **terjemahan melalui HTTP**)

- **UI**: Mengedit .env, mendaftarkan dan mengirim tujuan, melihat log, **terjemahan file (prabaca langsung)**, otomatis memulai Relay saat dalam mode lokal

- **Console**: Mengikat & mengirim dari terminal. Menampilkan tail log

> Yang diperlukan: **Discord Bot Token** dan **OpenAI API Key** (konfigurasi tanpa memanggil OpenAI secara langsung juga diperbolehkan)

---

## Daftar Isi

- [Konfigurasi](#%E6%A7%8B%E6%88%90)

- [Persyaratan](#%E8%A6%81%E4%BB%B6)

- [.env (contoh minimal)](#env%E6%9C%80%E5%B0%8F%E4%BE%8B)

- [Cara Menggunakan](#%E4%BD%BF%E3%81%84%E6%96%B9)
  
  - [A. Menggunakan UI + Relay secara lokal](#a-%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E3%81%A7-ui--relay)
  
  - [B. Menghubungkan ke Relay jarak jauh](#b-%E3%83%AA%E3%83%A2%E3%83%BC%E3%83%88-relay-%E3%81%AB%E6%8E%A5%E7%B6%9A)
  
  - [C. Console (terminal)](#c-console%E3%82%BF%E3%83%BC%E3%83%9F%E3%83%8A%E3%83%AB)

- [API (Relay)](#apirelay)
  
  - [/translate (r3 baru)](#translater3-%E6%96%B0%E8%A6%8F)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [Log (JSONL)](#%E3%83%AD%E3%82%B0jsonl)

- [Contoh integrasi dengan VS Code Wrapper](#vs-code-%E3%83%A9%E3%83%83%E3%83%91%E3%83%BC%E9%80%A3%E6%90%BA%E4%BE%8B)

- [Pertanyaan yang Sering Diajukan](#%E3%82%88%E3%81%8A%E3%81%8A%E3%82%8B%E8%B3%AA%E5%95%8F)

- [Tips Pengembangan/Pemeliharaan](#%E9%96%8B%E7%99%BA%E9%81%8B%E7%94%A8tips)

- [Lisensi](#%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9)

---

## Konfigurasi (File Utama)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # UI Desktop (Tkinter)
IMTB-D_console.py    # Console untuk terminal
console_routes.json      # Penyimpanan tujuan (ditulis oleh UI)
log/messages.jsonl       # Log terjemahan (JSON Lines)
```

---

## Persyaratan

- Unduh file utama
- Python 3.10+ (lingkungan yang dapat menggunakan Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (contoh minimal)

Buat file `.env` di direktori utama repositori ini.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# URL dasar Relay (disarankan 127.0.0.1 saat menjalankan UI secara lokal)
IMTBD_API_BASE=http://127.0.0.1:8765

# Pengaturan bind Relay (Listen) (default: 127.0.0.1:8765 jika tidak diatur)
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# (Opsional) Lokasi penyimpanan log terjemahan
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Opsional) Terkait terjemahan
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Saat menggunakan UNC di Linux/mac, lebih baik untuk memasangnya terlebih dahulu dan menentukan jalur biasa. *IMTBD_JSONL_PATH adalah **case-sensitive** (Linux)*

---

## Cara Menggunakan

### A. Menggunakan UI + Relay secara lokal (paling cepat)

```bash
python IMTB-D_ui.py
```

- Jika `IMTBD_API_BASE` adalah `http://127.0.0.1:8765` atau `localhost`,  
  UI akan **secara otomatis membantu memulai Relay** (setelah dimulai akan menampilkan "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Dari tab "Setup", edit `.env` dan **Simpan .env**.

- Di tab "Destinations", **Bind** tujuan (DM/Channel) → masukkan teks → **Kirim**.
  
  ![destinations.png](docs/images/destinations.png)

- Log di bagian bawah akan mencerminkan pengiriman dan penerimaan.
  
  - Dengan tujuan (DM/Channel) yang dipilih, klik "Open Window" → layar obrolan individu akan terbuka.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Terjemahan teks
    
    - Masukkan teks di kotak di bagian bawah jendela, tekan kirim atau Enter untuk mengirim.
    
    - Jika perlu memasukkan beberapa baris, Anda dapat menggunakan Ctrl+Enter untuk membuat baris baru.
  
  - Terjemahan Gambar (Inpaint)
    
    - Lakukan terjemahan gambar dengan cara drag & drop.
    
    - Saat ini hasilnya mungkin tidak terlalu baik, tetapi dapat digunakan sebagai referensi.
      
      Sebelum terjemahan
      
      ![origin.png](docs/images/origin.png)
      
      Setelah terjemahan
      
      ![translated.png](docs/images/translated.png)

### B. Menghubungkan ke Relay jarak jauh (contoh: Raspberry Pi)

- Jalankan `IMTB-D_relay.py` di server (Pi, dll),
- Atur `IMTBD_API_BASE` di `.env` sisi UI ke `http://<server-ip>:8765`.  
- Dalam hal ini, Start/Stop UI dinonaktifkan dan berfungsi dalam **mode jarak jauh**.

### C. Console (terminal)

```bash
# Ke channel
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Ke DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Mengetik langsung ke input standar akan mengirim (log ditampilkan dalam mode tail).
```

---

## API (Relay)

### `/translate` (r3 baru)

**API umum yang menerjemahkan teks yang diterima melalui HTTP dan mengembalikan terjemahan melalui HTTP**. Tidak melalui Discord.

- **POST** `/translate`

- **Request (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""` (tidak ditentukan/auto/kosong akan diidentifikasi secara otomatis)
  
  - `target`: default adalah `DEFAULT_REPLY_LANG` di `.env` (contoh: `"ja"`)

- **Response (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **Contoh: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **Contoh: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### Janji nilai kembali

- Ketika `ok` adalah `true`, `translated` berisi terjemahan

- Jika gagal, akan mengembalikan `{ "ok": false, "error": "<message>" }` (HTTP 4xx/5xx)

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — Mendaftarkan nama console dan tujuan (dm/channel, id, lang, dll)

- `POST /send` — Mengirim teks ke console yang ditentukan (dikirim ke sisi Discord)

- `POST /send_image` — Gambar OCR → terjemahan → inpaint → kirim

- `GET /stats` — Status aktif dan daftar binding> `/translate` adalah **untuk membalas langsung ke klien HTTP**, sehingga sangat cocok untuk integrasi dengan alat eksternal seperti VS Code. Alur melalui Discord yang tradisional menggunakan `/bind` dan `/send`.

---

## Log (JSONL)

- Default: `log/messages.jsonl`. Anda dapat mengubah lokasi penyimpanan di `.env` dengan `IMTBD_JSONL_PATH`.  
- UI akan men-tail file ini dan menampilkannya di layar. Dapat diakses bahkan melalui UNC share.

---

## Contoh Integrasi Wrapper VS Code

- Pengaturan di ekstensi: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- Pilih → **Ganti Pilihan dengan Bahasa Jepang** (contoh: `Ctrl+Alt+K`) untuk **penggantian langsung**

- Terjemahan clipboard (`Ctrl+Alt+J`), terjemahan hover, dll. mengikuti pengaturan di ekstensi

---

## Pertanyaan yang Sering Diajukan (FAQ)

**Q: Bagaimana cara menulis path UNC di Windows?**  
A: Di `.env`, tulis `\\raspberrypi\IMTB-D\messages.jsonl` dengan **dua backslash**.  
   Karena alasan escape di dalam `.env`, sebaiknya tulis sebagai `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

**Q: Muncul `fetch failed`**  
A: `localhost` mungkin terhubung dengan IPv6 dan tidak dapat diakses. Cobalah dengan **`127.0.0.1`**. Untuk remote, gunakan `<server-ip>`.

**Q: Permission denied (tulisan `console_routes.json`)**  
A: Editor mungkin masih membuka file (eksklusif) atau disebabkan oleh Controlled Folder Access di Windows. Ubah lokasi penyimpanan ke direktori pengguna atau tutup editor dan jalankan kembali.

---

## Tips Pengembangan/Operasional

- **Hot Reload r3** (restart saat menyimpan)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **Menjalankan secara permanen (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Penggunaan Git**
  
  - Komit implementasi `/translate`, README, dan CHANGELOG
  
  - Jangan komit `.env` (sediakan `.env.example`)
  
  - Secara prinsip, abaikan `.vscode/`. Jika ingin dibagikan, hanya sertakan yang tidak bersifat rahasia seperti `extensions.json`/`tasks.json` yang paling minimal

---

## Lisensi

Lisensi MIT