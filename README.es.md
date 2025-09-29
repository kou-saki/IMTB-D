## Traductor Multilingüe Interactivo BOT para Discord (IMTB-D)

Una herramienta que combina un **Bot de traducción Relay** que puede traducir y leer mensajes de Discord en “el idioma que desees”, una **UI de escritorio (Tkinter)** para controlarlo desde tu dispositivo, y una **Consola** que se puede usar desde la terminal.  
Los registros de traducción se pueden guardar en **JSONL**, y también se puede especificar una ruta de compartición UNC (ej: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Bot de Discord y API HTTP local (`/bind`, `/send`, `/send_image`, `/stats`)

- **Adición de Relay r3**: **`/translate`** (recibe texto por HTTP y devuelve **la traducción por HTTP**)

- **UI**: Edición de .env, registro y envío de destinos, visualización de registros, **traducción de archivos (vista previa en vivo)**, inicio automático de Relay en modo local

- **Consola**: Vinculación y envío desde la terminal. Visualización de registros en tiempo real

> Requisitos: **Token de Bot de Discord** y **Clave de API de OpenAI** (también es posible una configuración sin acceso directo a OpenAI)

---

## Tabla de Contenidos

- [Configuración](#%E6%A7%8B%E6%88%90)

- [Requisitos](#%E8%A6%81%E4%BB%B6)

- [.env (ejemplo mínimo)](#env%E6%9C%80%E5%B0%8F%E4%BE%8B)

- [Uso](#%E4%BD%BF%E3%81%84%E6%96%B9)
  
  - [A. Usar UI + Relay localmente](#a-%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E3%81%A7-ui--relay)
  
  - [B. Conectar a Relay remoto](#b-%E3%83%AA%E3%83%A2%E3%83%BC%E3%83%88-relay-%E3%81%AB%E6%8E%A5%E7%B6%9A)
  
  - [C. Consola (terminal)](#c-console%E3%82%BF%E3%83%BC%E3%83%9F%E3%83%8A%E3%83%AB)

- [API (Relay)](#apirelay)
  
  - [/translate (nueva r3)](#translater3-%E6%96%B0%E8%A6%8F)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [Registros (JSONL)](#%E3%83%AD%E3%82%B0jsonl)

- [Ejemplo de integración con VS Code Wrapper](#vs-code-%E3%83%A9%E3%83%83%E3%83%91%E3%83%BC%E9%80%A3%E6%90%BA%E4%BE%8B)

- [Preguntas frecuentes](#%E3%82%88%E3%81%8F%E3%81%82%E3%82%8B%E8%B3%AA%E5%95%8F)

- [Consejos de desarrollo/operación](#%E9%96%8B%E7%99%BA%E9%81%8B%E7%94%A8tips)

- [Licencia](#%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9)

---

## Configuración (archivos principales)

```
IMTB-D_relay.py      # Bot de Discord + API HTTP
IMTB-D_ui.py         # UI de escritorio (Tkinter)
IMTB-D_console.py    # Consola para terminal
console_routes.json      # Almacenamiento de destinos (escrito por UI)
log/messages.jsonl       # Registros de traducción (JSON Lines)
```

---

## Requisitos

- Descargar los archivos principales
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

# URL base de Relay (se recomienda 127.0.0.1 para uso local de UI)
IMTBD_API_BASE=http://127.0.0.1:8765

# Configuración de vinculación (Listen) de Relay (por defecto: 127.0.0.1:8765 si no se configura)
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# (opcional) Ruta de almacenamiento de registros de traducción
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (opcional) Configuración relacionada con la traducción
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Al usar UNC en Linux/mac, es recomendable montar previamente y especificar la ruta normal. *IMTBD_JSONL_PATH es **sensible a mayúsculas y minúsculas** (Linux)*

---

## Uso

### A. Usar UI + Relay localmente (más rápido)

```bash
python IMTB-D_ui.py
```

- Si `IMTBD_API_BASE` es `http://127.0.0.1:8765` o `localhost`,  
  la UI **ayudará automáticamente a iniciar Relay** (después de iniciar, mostrará "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Edita `.env` desde la pestaña "Setup" y **guarda .env**.

- En la pestaña "Destinations", **vincula** un destino (DM/Canal) → ingresa texto → **envía**.
  
  ![destinations.png](docs/images/destinations.png)

- Los envíos y recepciones se reflejarán en el registro en la parte inferior.
  
  - Con un destino (DM/Canal) seleccionado, haz clic en "Open Window" → se abrirá la pantalla de chat individual.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Traducción de texto
    
    - Ingresa texto en el cuadro en la parte inferior de la ventana y presiona enviar o Enter para enviar.
    
    - Si necesitas ingresar múltiples líneas, puedes usar Ctrl+Enter para hacer un salto de línea.
  
  - Traducción de imágenes (Inpaint)
    
    - Puedes arrastrar y soltar imágenes para realizar la traducción de imágenes mediante el método de inpainting.
    
    - En esta etapa, la calidad no es muy buena, pero puede servir como referencia.
      
      Antes de la traducción
      
      ![origin.png](docs/images/origin.png)
      
      Después de la traducción
      
      ![translated.png](docs/images/translated.png)

### B. Conectar a Relay remoto (ej: Raspberry Pi)

- Inicia `IMTB-D_relay.py` en el servidor (Pi, etc.), y
- Configura `IMTBD_API_BASE` en el `.env` de la UI a `http://<server-ip>:8765`.  
- En este caso, el inicio/parada de la UI estará deshabilitado y funcionará en **modo remoto**.

### C. Consola (terminal)

```bash
# Para canal
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Para DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Simplemente escribe en la entrada estándar para enviar (los registros se mostrarán en tiempo real).
```

---

## API (Relay)

### `/translate` (nueva r3)

**API genérica que traduce texto recibido por HTTP y devuelve la traducción por HTTP**. No pasa por Discord.

- **POST** `/translate`

- **Request (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""` (no especificado/auto/vacío se determina automáticamente)
  
  - `target`: por defecto es `DEFAULT_REPLY_LANG` en `.env` (ej: `"ja"`)

- **Response (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **Ejemplo: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **Ejemplo: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### Promesas de retorno

- Cuando `ok` es `true`, `translated` contendrá la traducción

- En caso de fallo, devolverá `{ "ok": false, "error": "<message>" }` (HTTP 4xx/5xx)

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — Registra el nombre de la consola y el destino (dm/canal, id, lang, etc.)

- `POST /send` — Envía texto a la consola especificada (entrega a Discord)

- `POST /send_image` — OCR de imagen → traducción → inpainting → envío

- `GET /stats` — Estado de inicio y lista de vinculaciones> `/translate` es **la respuesta directa al cliente HTTP**, lo que lo hace ideal para integraciones con herramientas externas como VS Code. El flujo tradicional a través de Discord utiliza `/bind` y `/send`.

---

## Registro (JSONL)

- Predeterminado: `log/messages.jsonl`. Puedes cambiar la ubicación de guardado en `.env` con `IMTBD_JSONL_PATH`.  
- La interfaz de usuario hace un tail de este archivo para mostrarlo en pantalla. También es accesible a través de comparticiones UNC.

---

## Ejemplo de integración con el envoltorio de VS Code

- Configuración del lado de la extensión: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- Selección → **Reemplazar selección con japonés** (ej: `Ctrl+Alt+K`) para **reemplazo en el lugar**

- La traducción del portapapeles (`Ctrl+Alt+J`), traducción al pasar el cursor, etc., se rigen por la configuración del lado de la extensión.

---

## Preguntas frecuentes (FAQ)

**Q: ¿Cómo se escribe la ruta UNC en Windows?**  
A: En `.env`, se debe escribir `\\raspberrypi\IMTB-D\messages.jsonl` con **dos barras invertidas**.  
   Debido a la necesidad de escape en `.env`, lo más seguro es escribir `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

**Q: Aparece `fetch failed`**  
A: Puede que `localhost` esté resolviendo a IPv6 y no pueda conectarse. Prueba con **`127.0.0.1`**. Para conexiones remotas, utiliza `<server-ip>`.

**Q: Permiso denegado (escritura en `console_routes.json`)**  
A: Puede ser que el editor tenga el archivo abierto (en exclusividad) o que el Acceso Controlado a Carpetas de Windows esté causando el problema. Cambia la ubicación de guardado al directorio del usuario o cierra el editor y vuelve a ejecutar.

---

## Consejos de desarrollo/operación

- **Recarga en caliente de r3** (reinicio al guardar)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **Ejecución en segundo plano (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Uso de Git**
  
  - Commitear la implementación de `/translate`, README y CHANGELOG.
  
  - No commitear `.env` (proporcionar `.env.example`).
  
  - Ignorar en principio `.vscode/`. Si se desea compartir, solo incluir lo mínimo sin información sensible como `extensions.json`/`tasks.json`, etc.

---

## Licencia

Licencia MIT