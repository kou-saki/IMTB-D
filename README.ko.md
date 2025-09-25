# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Discord 의 메시지를 “좋아하는 언어” 로 번역하여 읽고 쓸 수 있는 **번역 릴레이 Bot（Relay）**,
그것을 손에서 조작할 수 있는 **데스크탑 UI（Tkinter）**, 터미널에서 사용할 수 있는 **Console** 를 종합한 도구입니다.(2025/09/08 현재 지원: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th)
번역 로그는 **JSONL** 형식으로 저장할 수 있으며, UNC 공유 경로(예: `\\raspberrypi\IMTB-D\messages.jsonl`)도 지정 가능합니다.

- **Relay**: Discord Bot 과 로컬 HTTP API（`/bind`, `/send`, `/send_image`, `/stats`）。
- **UI**: .env 편집, 수신처 등록・전송, 로그 조회, **파일 번역（라이브 미리보기）**, 로컬일 경우 Relay 자동 시작.
- **Console**: 터미널에서 바인드 및 전송. 로그의 tail 표시.

> 필요한 것: **Discord Bot Token** 과 **OpenAI API Key**.

---

## 구성（주요 파일）

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # 데스크탑 UI（Tkinter）
IMTB-D_console.py    # 터미널용 콘솔
console_routes.json      # 수신처 저장（UI가 작성）
log/messages.jsonl       # 번역 로그（JSON Lines）
```

---

## 요구 사항

- 주요 파일 다운로드
- Python 3.10+（Tkinter 를 사용할 수 있는 환경）
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env（최소 예제）

이 리포지토리 바로 아래에 `.env` 를 생성합니다.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# 로컬에서 사용할 경우 localhost 를 권장（UI가 Relay 를 자동으로 시작）
IMTBD_API_BASE=http://127.0.0.1:8765

# （선택 사항）로그 저장 위치. Windows는 UNC, Linux/mac은 일반 경로로 OK
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# （선택 사항）번역 설정
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Linux/mac 에서 UNC 를 사용할 경우, 사전에 마운트하여 일반 경로로 지정하는 것이 확실합니다.※IMTBD_JSONL_PATH는 **대소문자를 구분**합니다（Linux）

---

## 사용 방법

### A. 로컬에서 UI + Relay 사용하기（최단）

```bash
python IMTB-D_ui.py
```

- `IMTBD_API_BASE` 가 `http://127.0.0.1:8765` 또는 `localhost` 인 경우,  
  UI 가 **Relay 의 시작을 자동으로 보조** 합니다（시작 후 "API ready" 라고 표시됨）。
  
  ![setup.png](docs/images/setup.png)
  
  "Setup" 탭에서 `.env` 를 편집하고 **Save .env**.

- "Destinations" 탭에서 수신처(DM/Channel)를 **Bind** → 텍스트 입력 → **Send**.
  
  ![destinations.png](docs/images/destinations.png)

- 하단의 로그에 송수신이 반영됩니다.
  
  - 수신처(DM/Channel)를 선택한 상태에서 "Open Window" 를 클릭→개별 채팅 화면이 열립니다.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - 텍스트 번역
    
    - 창 하단의 박스에 텍스트를 입력하고 send 또는 Enter 를 눌러 전송합니다.
    
    - 여러 줄 입력이 필요한 경우 Ctrl+Enter 로 줄바꿈할 수 있습니다.
  
  - 이미지 번역(Inpaint)
    
    - 이미지를 D&D 하여 인페인트 방식의 이미지 번역을 수행합니다.
    
    - 현재 단계에서는 그리 깨끗하지 않지만, 참고용으로는 됩니다.
      
      번역 전
      
      ![origin.png](docs/images/origin.png)
      
      번역 후
      
      ![translated.png](docs/images/translated.png)

### B. 원격 Relay (예: Raspberry Pi) 에 연결

- 서버(Pi 등)에서 `IMTB-D_relay.py` 를 실행해 두고,
- UI 쪽의 `.env` 의 `IMTBD_API_BASE` 를 `http://<server-ip>:8765` 로 설정.  
- 이 경우 UI 의 Start/Stop 는 비활성화되며, **원격 모드**로 동작합니다.

### C. Console（터미널）

```bash
# 채널로
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# DM 으로
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# 그대로 표준 입력에 입력하면 전송됩니다（로그는 tail 표시）。
```

---

## API（Relay）

- `POST /bind` — 콘솔 이름과 수신처（dm/channel, id, lang）를 등록  
- `POST /send` — 지정 콘솔로 텍스트 전송（`lang` 으로 일시적으로 덮어쓸 수 있음）  
- `POST /send_image` — 이미지의 OCR → 번역 → 인페인트＆그리기 → 전송  
- `GET  /stats` — 시작 상태・바인딩 목록

---

## 로그（JSONL）

- 기본: `log/messages.jsonl`。`.env` 의 `IMTBD_JSONL_PATH` 로 저장 위치를 변경할 수 있습니다.  
- UI 는 이 파일을 tail 하여 화면에 표시합니다. UNC 공유를 통해서도 열람 가능합니다.

---

## 자주 묻는 질문（FAQ）

**Q: Windows 의 UNC 경로는 어떻게 작성하나요?**  
A: `.env` 에서는 `\\raspberrypi\IMTB-D\messages.jsonl` 을 **백슬래시 2개**로 작성합니다.  
   `.env` 내의 이스케이프 상, 실제로는 `\\\\raspberrypi\\IMTB-D\\messages.jsonl` 로 작성하는 것이 안전합니다.

---

## 라이센스

MIT 라이센스