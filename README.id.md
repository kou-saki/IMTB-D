# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Bot **翻訳リレー（Relay）** yang dapat menerjemahkan pesan Discord ke dalam “bahasa yang diinginkan” dan membacanya, serta **UI Desktop (Tkinter)** untuk mengoperasikannya dari tangan Anda, dan **Console** yang dapat digunakan dari terminal. (Dukungan per 2025/09/08: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th) Log terjemahan dapat disimpan dalam **JSONL** dan juga dapat menentukan jalur berbagi UNC (contoh: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Discord Bot dan API HTTP lokal (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI**: Pengeditan .env, pendaftaran dan pengiriman tujuan, tampilan log, **terjemahan file (prabaca langsung)**, otomatis memulai Relay saat lokal.
- **Console**: Mengikat & mengirim dari terminal. Menampilkan tail log.

> Yang dibutuhkan: **Token Bot Discord** dan **Kunci API OpenAI**.

---

## Struktur (File Utama)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # UI Desktop (Tkinter)
IMTB-D_console.py    # Console untuk terminal
console_routes.json      # Penyimpanan tujuan (ditulis oleh UI)
log/messages.jsonl       # Log terjemahan (JSON Lines)
```

---

## Persyaratan

- Python 3.10+ (Lingkungan yang dapat menggunakan Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (Contoh Minimal)

Buat file `.env` di direktori utama repositori ini.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Untuk penggunaan lokal, disarankan menggunakan localhost (UI otomatis memulai Relay)
IMTBD_API_BASE=http://127.0.0.1:8765

# (Opsional) Lokasi penyimpanan log. Windows menggunakan UNC, Linux/mac menggunakan jalur biasa
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Opsional) Pengaturan terjemahan
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Saat menggunakan UNC di Linux/mac, lebih baik untuk memasangnya terlebih dahulu dan menentukan jalur biasa. ※IMTBD_JSONL_PATH **membedakan huruf besar dan kecil** (Linux)

---

## Cara Menggunakan

### A. Menggunakan UI + Relay secara lokal (Cara Tercepat)

```bash
python IMTB-D_ui.py
```

- Jika `IMTBD_API_BASE` adalah `http://127.0.0.1:8765` atau `localhost`,  
  UI akan **secara otomatis membantu memulai Relay** (setelah dimulai akan menampilkan “API ready”).
  
  ![setup.png](docs/images/setup.png)
  
  Edit `.env` dari tab “Setup” dan **Simpan .env**.

- Di tab “Destinations”, **Bind** tujuan (DM/Channel) → masukkan teks → **Kirim**.
  
  ![destinations.png](docs/images/destinations.png)

- Log di bagian bawah akan mencerminkan pengiriman dan penerimaan.
  
  - Dengan tujuan (DM/Channel) yang dipilih, klik “Open Window” → layar obrolan individu akan terbuka.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Terjemahan Teks
    
    - Masukkan teks di kotak di bagian bawah jendela, tekan send atau Enter untuk mengirim.
    
    - Jika perlu memasukkan beberapa baris, Anda dapat menggunakan Ctrl+Enter untuk membuat baris baru.
  
  - Terjemahan Gambar (Inpaint)
    
    - Dengan menyeret dan menjatuhkan gambar, Anda dapat melakukan terjemahan gambar dengan metode inpaint.
    
    - Saat ini hasilnya mungkin tidak terlalu baik, tetapi dapat digunakan sebagai referensi.
      
      Sebelum terjemahan
      
      ![origin.png](docs/images/origin.png)
      
      Setelah terjemahan
      
      ![translated.png](docs/images/translated.png)

### B. Menghubungkan ke Relay Jarak Jauh (contoh: Raspberry Pi)

- Jalankan `IMTB-D_relay.py` di server (Pi, dll.),
- Atur `IMTBD_API_BASE` di `.env` UI ke `http://<server-ip>:8765`.  
- Dalam hal ini, Start/Stop UI dinonaktifkan dan berfungsi dalam **mode jarak jauh**.

### C. Console (Terminal)

```bash
# Ke channel
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Ke DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Ketik langsung di input standar untuk mengirim (log ditampilkan dalam tail).
```

---

## API (Relay)

- `POST /bind` — Mendaftarkan nama console dan tujuan (dm/channel, id, lang)  
- `POST /send` — Mengirim teks ke console yang ditentukan (dapat ditimpa sementara dengan `lang`)  
- `POST /send_image` — OCR gambar → terjemahan → inpaint & gambar → kirim  
- `GET  /stats` — Status aktif dan daftar binding

---

## Log (JSONL)

- Default: `log/messages.jsonl`. Anda dapat mengubah lokasi penyimpanan dengan `IMTBD_JSONL_PATH` di `.env`.  
- UI akan menampilkan file ini dalam tampilan tail. Dapat diakses melalui berbagi UNC.

---

## Pertanyaan Umum (FAQ)

**Q: Bagaimana cara menulis jalur UNC di Windows?**  
A: Di `.env`, tulis `\\raspberrypi\IMTB-D\messages.jsonl` dengan **dua backslash**.  
   Karena alasan escape di dalam `.env`, lebih baik menulisnya sebagai `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

---

## Lisensi

Lisensi MIT