# Интерактивный многоязычный переводчик BOT для Discord (IMTB-D)

**Бот для перевода сообщений Discord** в "любом языке" и их чтения и написания, **десктопный интерфейс (Tkinter)** для управления им с вашего устройства, а также **Консоль**, доступная из терминала. (Поддержка на 2025/09/08: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th) Логи переводов могут сохраняться в **JSONL** и можно указать UNC путь (например: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Discord Bot и локальный HTTP API (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI**: редактирование .env, регистрация и отправка получателей, просмотр логов, **перевод файлов (живой предварительный просмотр)**, автоматический запуск Relay при локальном использовании.
- **Console**: привязка и отправка из терминала. Отображение tail логов.

> Необходимое: **Токен Discord Bot** и **Ключ API OpenAI**.

---

## Структура (основные файлы)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Десктопный интерфейс (Tkinter)
IMTB-D_console.py    # Консоль для терминала
console_routes.json      # Сохранение получателей (запись из UI)
log/messages.jsonl       # Лог переводов (JSON Lines)
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

# Рекомендуется использовать localhost для локального использования (UI автоматически запускает Relay)
IMTBD_API_BASE=http://127.0.0.1:8765

# (по желанию) Путь для сохранения логов. Windows использует UNC, Linux/mac можно указать обычный путь
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (по желанию) Настройки перевода
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> При использовании UNC на Linux/mac, рекомендуется предварительно смонтировать и указывать обычный путь. *IMTBD_JSONL_PATH чувствителен к регистру* (Linux).

---

## Как использовать

### A. Использование UI + Relay локально (самый быстрый способ)

```bash
python IMTB-D_ui.py
```

- Если `IMTBD_API_BASE` установлен на `http://127.0.0.1:8765` или `localhost`,  
  UI **автоматически помогает запустить Relay** (после запуска отображается "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Вкладка «Setup» позволяет редактировать `.env` и **Сохранить .env**.

- Вкладка «Destinations» для привязки получателя (DM/Channel) → ввод текста → **Отправить**.
  
  ![destinations.png](docs/images/destinations.png)

- Логи отправки и получения отображаются внизу.
  
  - Нажмите «Open Window», чтобы открыть индивидуальное окно чата, выбрав получателя (DM/Channel).
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Перевод текста
    
    - Введите текст в поле внизу окна и нажмите send или Enter для отправки.
    
    - Для ввода нескольких строк используйте Ctrl+Enter для переноса строки.
  
  - Перевод изображения (Inpaint)
    
    - Перетащите изображение для выполнения перевода изображения методом инпейнта.
    
    - На данный момент результат может быть не очень качественным, но будет полезен для справки.
      
      Перед переводом
      
      ![origin.png](docs/images/origin.png)
      
      После перевода
      
      ![translated.png](docs/images/translated.png)

### B. Подключение к удаленному Relay (например, Raspberry Pi)

- Запустите `IMTB-D_relay.py` на сервере (Pi и т.д.),
- Установите `IMTBD_API_BASE` в `.env` на `http://<server-ip>:8765`.  
- В этом случае функции Start/Stop UI будут отключены, и он будет работать в **удаленном режиме**.

### C. Консоль (терминал)

```bash
# В канал
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# В DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Ввод текста напрямую отправляет сообщение (логи отображаются в tail).
```

---

## API (Relay)

- `POST /bind` — регистрация имени консоли и получателя (dm/channel, id, lang)  
- `POST /send` — отправка текста в указанную консоль (временное переопределение `lang`)  
- `POST /send_image` — OCR изображения → перевод → инпейнт и рисование → отправка  
- `GET  /stats` — состояние запуска и список привязок

---

## Логи (JSONL)

- По умолчанию: `log/messages.jsonl`. Путь для сохранения можно изменить в `IMTBD_JSONL_PATH` в `.env`.  
- UI отслеживает этот файл и отображает его содержимое. Доступно для просмотра даже через UNC.

---

## Часто задаваемые вопросы (FAQ)

**Q: Как записать UNC путь для Windows?**  
A: В `.env` укажите `\\raspberrypi\IMTB-D\messages.jsonl` с **двойными обратными слешами**.  
   Внутри `.env` для экранирования лучше записать как `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

---

## Лицензия

MIT лицензия