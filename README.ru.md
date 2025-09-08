# Интерактивный многоязычный переводчик BOT для Discord (IMTB-D)

Инструмент, который позволяет переводить сообщения Discord на “любимый язык” и писать их с помощью **переводческого реле Bot (Relay)**, управляемого с помощью **десктопного интерфейса (Tkinter)** и доступного через **консоль** в терминале. (На данный момент поддерживаются: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th, по состоянию на 2025/09/08) Логи переводов могут быть сохранены в **JSONL** и также можно указать UNC путь для общего доступа (например: `\\raspberrypi\IMTB-D\messages.jsonl`).

- **Relay**: Discord Bot и локальный HTTP API (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI**: редактирование .env, регистрация и отправка получателей, просмотр логов, **перевод файлов (живой предварительный просмотр)**, автоматический запуск Relay при локальном использовании.
- **Console**: привязка и отправка из терминала. Отображение tail логов.

> Необходимые вещи: **Discord Bot Token** и **OpenAI API Key**.

---

## Структура (основные файлы)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # Десктопный интерфейс (Tkinter)
IMTB-D_console.py    # Консоль для терминала
console_routes.json      # Сохранение получателей (запись UI)
log/messages.jsonl       # Лог переводов (JSON Lines)
```

---

## Требования

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

# (необязательно) Путь для сохранения логов. Для Windows используйте UNC, для Linux/mac обычно достаточно обычного пути
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (необязательно) Настройки перевода
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> При использовании UNC на Linux/mac, рекомендуется предварительно смонтировать и указывать обычный путь. *IMTBD_JSONL_PATH **чувствителен к регистру** (Linux)*

---

## Как использовать

### A. Использование UI + Relay локально (самый быстрый способ)

```bash
python IMTB-D_ui.py
```

- Если `IMTBD_API_BASE` установлен на `http://127.0.0.1:8765` или `localhost`,  
  UI **автоматически поможет запустить Relay** (после запуска будет отображаться «API ready»).
  
  ![setup.png](docs/images/setup.png)
  
  Вкладка «Setup» позволяет редактировать `.env` и **Сохранить .env**.

- На вкладке «Destinations» выберите получателя (DM/Channel) и **Bind** → введите текст → **Send**.
  
  ![destinations.png](docs/images/destinations.png)

- В нижней части лога будут отображаться отправленные и полученные сообщения.
  
  - Выберите получателя (DM/Channel) и нажмите «Open Window» → откроется окно индивидуального чата.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Перевод текста
    
    - Введите текст в поле внизу окна и нажмите send или Enter для отправки.
    
    - Для ввода нескольких строк используйте Ctrl+Enter для переноса строки.
  
  - Перевод изображений (Inpaint)
    
    - Перетащите изображение для выполнения перевода изображения с помощью метода инпейнта.
    
    - На данный момент результат не очень качественный, но может быть полезен для справки.
      
      Перед переводом
      
      ![origin.png](docs/images/origin.png)
      
      После перевода
      
      ![translated.png](docs/images/translated.png)

### B. Подключение к удаленному Relay (например, Raspberry Pi)

- Запустите `IMTB-D_relay.py` на сервере (например, Pi),
- Установите `IMTBD_API_BASE` в `.env` на `http://<server-ip>:8765`.  
- В этом случае функции Start/Stop UI будут отключены, и он будет работать в **удаленном режиме**.

### C. Консоль (терминал)

```bash
# В канал
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# В DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Просто введите текст в стандартный ввод, и он будет отправлен (лог будет отображаться в режиме tail).
```

---

## API (Relay)

- `POST /bind` — регистрация имени консоли и получателя (dm/channel, id, lang)  
- `POST /send` — отправка текста в указанную консоль (временное переопределение `lang`)  
- `POST /send_image` — OCR изображения → перевод → инпейнт и отрисовка → отправка  
- `GET  /stats` — состояние запуска и список привязок

---

## Логи (JSONL)

- По умолчанию: `log/messages.jsonl`. Путь для сохранения можно изменить в `.env` на `IMTBD_JSONL_PATH`.  
- UI будет отслеживать этот файл и отображать его на экране. Доступно для просмотра даже через UNC.

---

## Часто задаваемые вопросы (FAQ)

**Q: Как записать UNC путь для Windows?**  
A: В `.env` укажите `\\raspberrypi\IMTB-D\messages.jsonl` с **двумя обратными слэшами**.  
   Из-за экранирования в `.env`, на самом деле лучше записать как `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

---

## Лицензия

MIT лицензия