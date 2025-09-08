# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Bot de **traducción Relay** que permite leer y escribir mensajes de Discord en el “idioma que prefieras”,  
junto con una **UI de escritorio (Tkinter)** para controlarlo desde tu dispositivo, y una **Consola** que se puede usar desde la terminal. (Soporte actual a partir del 2025/09/08: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th)  
Los registros de traducción se pueden guardar en **JSONL** y se puede especificar una ruta de compartición UNC (ej: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Bot de Discord y API HTTP local (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI**: Edición de .env, registro y envío de destinos, visualización de registros, **traducción de archivos (vista previa en vivo)**, inicio automático de Relay en modo local.
- **Console**: Vinculación y envío desde la terminal. Visualización de tail de registros.

> Requisitos: **Token de Bot de Discord** y **Clave de API de OpenAI**.

---

## Estructura (archivos principales)

```
IMTB-D_relay.py      # Bot de Discord + API HTTP
IMTB-D_ui.py         # UI de escritorio (Tkinter)
IMTB-D_console.py    # Consola para terminal
console_routes.json      # Almacenamiento de destinos (escritura desde UI)
log/messages.jsonl       # Registro de traducción (JSON Lines)
```

---

## Requisitos

- Python 3.10+ (entorno donde se puede usar Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (ejemplo mínimo)

Crea un archivo `.env` en la raíz de este repositorio.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Se recomienda usar localhost para uso local (UI inicia Relay automáticamente)
IMTBD_API_BASE=http://127.0.0.1:8765

# (opcional) Ruta de almacenamiento de registros. Windows usa UNC, Linux/mac puede usar ruta normal
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (opcional) Configuración de traducción
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Al usar UNC en Linux/mac, es seguro montarlo previamente y especificar la ruta normal. ※IMTBD_JSONL_PATH **distingue entre mayúsculas y minúsculas** (Linux)

---

## Cómo usar

### A. Usar UI + Relay localmente (más corto)

```bash
python IMTB-D_ui.py
```

- Si `IMTBD_API_BASE` es `http://127.0.0.1:8765` o `localhost`,  
  la UI **ayudará automáticamente a iniciar Relay** (después de iniciar, se mostrará "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Edita `.env` desde la pestaña "Setup" y **guarda .env**.

- En la pestaña "Destinations", **Vincula** el destino (DM/Canal) → ingresa texto → **Envía**.
  
  ![destinations.png](docs/images/destinations.png)

- Los envíos y recepciones se reflejarán en el registro en la parte inferior.
  
  - Con el destino (DM/Canal) seleccionado, haz clic en "Open Window" → se abrirá la ventana de chat individual.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Traducción de texto
    
    - Ingresa texto en el cuadro en la parte inferior de la ventana y presiona enviar o Enter para enviar.
    
    - Si necesitas ingresar varias líneas, puedes usar Ctrl+Enter para hacer un salto de línea.
  
  - Traducción de imágenes (Inpaint)
    
    - Puedes arrastrar y soltar imágenes para realizar traducción de imágenes mediante el método de inpainting.
    
    - En esta etapa, la calidad no es muy buena, pero puede servir como referencia.
      
      Antes de la traducción
      
      ![origin.png](docs/images/origin.png)
      
      Después de la traducción
      
      ![translated.png](docs/images/translated.png)

### B. Conectar a Relay remoto (ej: Raspberry Pi)

- Inicia `IMTB-D_relay.py` en el servidor (Pi, etc.),  
- Configura `IMTBD_API_BASE` en el archivo `.env` de la UI a `http://<server-ip>:8765`.  
- En este caso, el inicio/parada de la UI estará deshabilitado y funcionará en **modo remoto**.

### C. Consola (terminal)

```bash
# Para canal
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Para DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Simplemente escribe en la entrada estándar para enviar (los registros se mostrarán en tail).
```

---

## API (Relay)

- `POST /bind` — Registra el nombre de la consola y el destino (dm/canal, id, lang)  
- `POST /send` — Envía texto a la consola especificada (se puede sobrescribir temporalmente con `lang`)  
- `POST /send_image` — OCR de imagen → traducción → inpainting y dibujo → envío  
- `GET  /stats` — Estado de inicio y lista de vinculaciones

---

## Registros (JSONL)

- Predeterminado: `log/messages.jsonl`. Puedes cambiar la ruta de almacenamiento con `IMTBD_JSONL_PATH` en `.env`.  
- La UI hace tail de este archivo para mostrarlo en pantalla. También se puede ver a través de comparticiones UNC.

---

## Preguntas frecuentes (FAQ)

**Q: ¿Cómo se escribe la ruta UNC en Windows?**  
A: En `.env`, debes escribir `\\raspberrypi\IMTB-D\messages.jsonl` con **dos barras invertidas**.  
   Debido a la necesidad de escape en `.env`, es más seguro escribir `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

---

## Licencia

Licencia MIT