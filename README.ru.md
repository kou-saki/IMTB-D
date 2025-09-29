## Интерактивный многоязычный переводчик BOT для Discord (IMTB-D)

Инструмент, который позволяет переводить сообщения Discord на "любимый язык" и отправлять их с помощью **переводческого реле Bot (Relay)**, управляемого с помощью **десктопного интерфейса (Tkinter)** и доступного через **консоль**.  
Журнал переводов может быть сохранен в **JSONL** и также можно указать UNC путь (например: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Discord Bot и локальный HTTP API (`/bind`, `/send`, `/send_image`, `/stats`)

- **Дополнение Relay r3**: **`/translate`** (принимает текст по HTTP и возвращает **переведенный текст через HTTP**)

- **UI**: редактирование .env, регистрация и отправка получателей, просмотр журнала, **перевод файлов (живой предварительный просмотр)**, автоматический запуск Relay при локальном использовании

- **Консоль**: привязка и отправка из терминала. Отображение tail журнала

> Необходимое: **Discord Bot Token** и **OpenAI API Key** (можно использовать конфигурацию без прямого обращения к OpenAI)

---

## Содержание

- [Конфигурация](#%E6%A7%8B%E6%88%90)

- [Требования](#%E8%A6%81%E4%BB%B6)

- [.env (минимальный пример)](#env%E6%9C%80%E5%B0%8F%E4%BE%8B)

- [Использование](#%E4%BD%BF%E3%81%84%E6%96%B9)
  
  - [A. Локальное использование UI + Relay](#a-%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E3%81%A7-ui--relay)
  
  - [B. Подключение к удаленному Relay](#b-%E3%83%AA%E3%83%A2%E3%83%BC%E3%83%88-relay-%E3%81%AB%E6%8E%A5%E7%B6%9A)
  
  - [C. Консоль (терминал)](#c-console%E3%82%BF%E3%83%BC%E3%83%9F%E3%83%8A%E3%83%AB)

- [API (Relay)](#apirelay)
  
  - [/translate (новый r3)](#translater3-%E6%96%B0%E8%A6%8F)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [Журнал (JSONL)](#%E3%83%AD%E3%82%B0jsonl)

- [Пример интеграции с VS Code](#vs-code-%E3%83%A9%E3%83%83%E3%83%91%E3%83%BC%E9%80%A3%E6%90%BA%E4%BE%8B)

- [Часто задаваемые вопросы](#%E3%82%88%E3%81%8F%E3%81%82%E3%82%8B%E8%B3%AA%E5%95%8F)

- [Советы по разработке/эксплуатации](#%E9%96%8B%E7%99%BA%E9%81%8B%E7%94%A8tips)

- [Лицензия](#%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9)

---

## Конфигурация (основные файлы)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Десктопный UI (Tkinter)
IMTB-D_console.py    # Консоль для терминала
console_routes.json      # Сохранение получателей (запись из UI)
log/messages.jsonl       # Журнал переводов (JSON Lines)
```

---

## Требования

- Скачайте основные файлы
- Python 3.10+ (среда, поддерживающая Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (минимальный пример)

Создайте файл `.env` в корне этого репозитория.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Базовый URL для Relay (рекомендуется 127.0.0.1 при локальной работе UI)
IMTBD_API_BASE=http://127.0.0.1:8765

# Настройки привязки Relay (если не указано, по умолчанию: 127.0.0.1:8765)
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# (необязательно) Путь для сохранения журнала переводов
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (необязательно) Связанные с переводом
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> При использовании UNC на Linux/mac лучше заранее смонтировать и указать путь в обычном формате. *IMTBD_JSONL_PATH чувствителен к регистру* (Linux)

---

## Использование

### A. Локальное использование UI + Relay (самый быстрый способ)

```bash
python IMTB-D_ui.py
```

- Если `IMTBD_API_BASE` установлен на `http://127.0.0.1:8765` или `localhost`,  
  UI **автоматически поможет запустить Relay** (после запуска будет отображено "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Вкладка "Setup" позволяет редактировать `.env` и **Сохранить .env**.

- На вкладке "Destinations" выберите получателя (DM/Channel) → **Bind** → введите текст → **Send**.
  
  ![destinations.png](docs/images/destinations.png)

- В нижней части журнала будут отображены отправленные и полученные сообщения.
  
  - Выберите получателя (DM/Channel) и нажмите "Open Window" → откроется окно индивидуального чата.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Перевод текста
    
    - Введите текст в поле внизу окна и нажмите send или Enter для отправки.
    
    - Для ввода нескольких строк используйте Ctrl+Enter для переноса строки.
  
  - Перевод изображений (Inpaint)
    
    - Перетащите изображение для выполнения перевода изображения методом инпейнта.
    
    - На данный момент результат может быть не очень качественным, но может служить ориентиром.
      
      Перед переводом
      
      ![origin.png](docs/images/origin.png)
      
      После перевода
      
      ![translated.png](docs/images/translated.png)

### B. Подключение к удаленному Relay (например, Raspberry Pi)

- Запустите `IMTB-D_relay.py` на сервере (например, Pi),
- Установите `IMTBD_API_BASE` в `.env` на `http://<server-ip>:8765`.  
- В этом случае кнопки Start/Stop в UI будут отключены, и программа будет работать в **удаленном режиме**.

### C. Консоль (терминал)

```bash
# Для канала
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Для DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Ввод текста напрямую в стандартный ввод отправит сообщение (журнал будет отображаться в режиме tail).
```

---

## API (Relay)

### `/translate` (новый r3)

**Общий API, который переводит текст, полученный по HTTP, и возвращает перевод по HTTP**. Не проходит через Discord.

- **POST** `/translate`

- **Запрос (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""` (не указано/auto/пустое значение автоматически определяется)
  
  - `target`: по умолчанию `.env` значение `DEFAULT_REPLY_LANG` (например: `"ja"`)

- **Ответ (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **Пример: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **Пример: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### Обещания возвращаемых значений

- Если `ok` равно `true`, то `translated` содержит перевод

- В случае ошибки возвращается `{ "ok": false, "error": "<message>" }` (HTTP 4xx/5xx)

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — регистрирует имя консоли и получателя (dm/channel, id, lang и т.д.)

- `POST /send` — отправляет текст на указанную консоль (доставляется на сторону Discord)

- `POST /send_image` — изображение OCR → перевод → инпейнт → отправка

- `GET /stats` — состояние запуска и список привязок> `/translate` является **оптимальным для прямого ответа HTTP-клиенту**, что делает его идеальным для интеграции с внешними инструментами, такими как VS Code. Традиционный поток через Discord использует `/bind` и `/send`.

---

## Логи (JSONL)

- По умолчанию: `log/messages.jsonl`. Место сохранения можно изменить с помощью `IMTBD_JSONL_PATH` в `.env`.  
- UI отслеживает этот файл и отображает его на экране. Доступен для просмотра даже через UNC-общие ресурсы.

---

## Пример интеграции с оберткой VS Code

- Настройка на стороне расширения: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- Выбор → **Заменить выбор на японский** (например, `Ctrl+Alt+K`) для **замены на месте**

- Перевод из буфера обмена (`Ctrl+Alt+J`), перевод при наведении и другие функции соответствуют настройкам на стороне расширения

---

## Часто задаваемые вопросы (FAQ)

**Q: Как записать UNC путь в Windows?**  
A: В `.env` укажите `\\raspberrypi\IMTB-D\messages.jsonl` с **двумя обратными слэшами**.  
   Из-за экранирования в `.env` на практике лучше записывать как `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

**Q: Появляется `fetch failed`**  
A: Возможно, `localhost` разрешается в IPv6 и не может подключиться. Попробуйте **`127.0.0.1`**. Для удаленного подключения используйте `<server-ip>`.

**Q: Permission denied (запись в `console_routes.json`)**  
A: Это может быть вызвано тем, что редактор оставил файл открытым (в эксклюзивном доступе) или из-за Controlled Folder Access в Windows. Измените место сохранения на пользовательский каталог или закройте редактор и повторите попытку.

---

## Советы по разработке/эксплуатации

- **Горячая перезагрузка r3** (перезапуск при сохранении)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **Запуск как служба (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Использование Git**
  
  - Коммитите реализацию `/translate`, README и CHANGELOG
  
  - `.env` не коммитите (предоставьте `.env.example`)
  
  - `.vscode/` в принципе игнорируйте. Если хотите поделиться, то только минимально необходимыми файлами без конфиденциальной информации, такими как `extensions.json`/`tasks.json`

---

## Лицензия

MIT лицензия