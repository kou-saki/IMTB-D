## 인터랙티브 다국어 번역기 BOT for Discord (IMTB-D)

Discord의 메시지를 “원하는 언어”로 번역하여 읽고 쓸 수 있는 **번역 릴레이 Bot (Relay)**, 이를 손쉽게 조작할 수 있는 **데스크탑 UI (Tkinter)**, 터미널에서 사용할 수 있는 **Console**을 통합한 도구입니다.  
번역 로그는 **JSONL** 형식으로 저장할 수 있으며, UNC 공유 경로(예: `\\raspberrypi\IMTB-D\messages.jsonl`)도 지정할 수 있습니다.

- **Relay**: Discord Bot과 로컬 HTTP API(`/bind`, `/send`, `/send_image`, `/stats`)

- **Relay r3 추가**: **`/translate`** (HTTP로 텍스트를 받아 **번역문을 HTTP로 반환하는 범용 API**)

- **UI**: .env 편집, 수신처 등록 및 전송, 로그 조회, **파일 번역(실시간 미리보기)**, 로컬일 경우 Relay 자동 시작

- **Console**: 터미널에서 바인드 및 전송. 로그의 tail 표시

> 필요한 것: **Discord Bot Token**과 **OpenAI API Key** (OpenAI에 직접 요청하지 않는 구성도 가능)

---

## 목차

- [구성](#%EA%B5%AC%EC%84%B1)

- [요건](#%EC%9A%94%EA%B5%AC)

- [.env (최소 예)](#env%EC%B5%9C%EC%86%8C%EC%98%88)

- [사용법](#%EC%82%AC%EC%9A%A9%EB%B2%95)
  
  - [A. 로컬에서 UI + Relay 사용하기](#a-%EB%A1%9C%EC%B0%AC%EC%97%90%EC%84%9C-ui--relay-%EC%82%AC%EC%9A%A9%ED%95%98%EA%B8%B0)
  
  - [B. 원격 Relay에 연결하기](#b-%EC%9B%90%EA%B0%9C-relay%EC%97%90-%EC%97%B0%EA%B2%B0%ED%95%98%EA%B8%B0)
  
  - [C. Console (터미널)](#c-console%ED%84%B0%EB%B0%8B%EB%84%90)

- [API (Relay)](#apirelay)
  
  - [/translate (r3 신규)](#translater3-%EC%83%88%EA%B7%9C)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [로그 (JSONL)](#%EB%A1%9C%EA%B7%B8jsonl)

- [VS Code 래퍼 연동 예시](#vs-code-%EB%9E%98%ED%8D%BC-%EC%97%B0%EB%8F%99-%EC%98%88%EC%8B%9C)

- [자주 묻는 질문](#%EC%9E%90%EC%A3%BC-%EB%AC%B5%EB%8B%88%EB%8A%94-%EC%A7%88%EB%AC%B8)

- [개발/운영 팁](#%EA%B0%9C%EB%B0%9C%EC%9A%B4%EC%98%81-%ED%8C%81)

- [라이센스](#%EB%9D%BC%EC%9D%B4%EC%84%B8%EC%8A%A4)

---

## 구성 (주요 파일)

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # 데스크탑 UI (Tkinter)
IMTB-D_console.py    # 터미널용 콘솔
console_routes.json      # 수신처 저장 (UI가 작성)
log/messages.jsonl       # 번역 로그 (JSON Lines)
```

---

## 요건

- 주요 파일 다운로드
- Python 3.10+ (Tkinter가 사용 가능한 환경)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (최소 예)

이 리포지토리의 최상위에 `.env` 파일을 생성합니다.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Relay의 기본 URL (UI의 로컬 운영 시 127.0.0.1 권장)
IMTBD_API_BASE=http://127.0.0.1:8765

# Relay 바인드 (Listen) 설정 (미설정 시 기본값: 127.0.0.1:8765)
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# (선택 사항) 번역 로그 저장 경로
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (선택 사항) 번역 관련
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Linux/mac에서 UNC를 사용할 때는 사전에 마운트하여 일반 경로로 지정하는 것이 확실합니다. ※IMTBD_JSONL_PATH는 **대소문자를 구분**합니다 (Linux).

---

## 사용법

### A. 로컬에서 UI + Relay 사용하기 (최단)

```bash
python IMTB-D_ui.py
```

- `IMTBD_API_BASE`가 `http://127.0.0.1:8765` 또는 `localhost`인 경우,  
  UI가 **Relay의 시작을 자동으로 보조**합니다 (시작 후 "API ready"가 표시됨).
  
  ![setup.png](docs/images/setup.png)
  
  "Setup" 탭에서 `.env`를 편집하고 **Save .env**를 클릭합니다.

- "Destinations" 탭에서 수신처 (DM/Channel)를 **Bind** → 텍스트 입력 → **Send**.
  
  ![destinations.png](docs/images/destinations.png)

- 하단의 로그에 송수신이 반영됩니다.
  
  - 수신처 (DM/Channel)를 선택한 상태에서 "Open Window"를 클릭하면 개별 채팅 화면이 열립니다.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - 텍스트 번역
    
    - 창 하단의 박스에 텍스트를 입력하고 send 또는 Enter를 눌러 전송합니다.
    
    - 여러 줄 입력이 필요한 경우 Ctrl+Enter로 줄바꿈할 수 있습니다.
  
  - 이미지 번역 (Inpaint)
    
    - 이미지를 드래그 앤 드롭하여 인페인팅 방식의 이미지 번역을 수행합니다.
    
    - 현재 단계에서는 그리 깔끔하지 않지만 참고용으로는 괜찮습니다.
      
      번역 전
      
      ![origin.png](docs/images/origin.png)
      
      번역 후
      
      ![translated.png](docs/images/translated.png)

### B. 원격 Relay에 연결하기 (예: Raspberry Pi)

- 서버(Pi 등)에서 `IMTB-D_relay.py`를 실행해 두고,
- UI 쪽의 `.env`에서 `IMTBD_API_BASE`를 `http://<server-ip>:8765`로 설정합니다.  
- 이 경우 UI의 Start/Stop는 비활성화되며, **원격 모드**로 동작합니다.

### C. Console (터미널)

```bash
# 채널로
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# DM으로
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# 그대로 표준 입력에 입력하면 전송됩니다 (로그는 tail 표시).
```

---

## API (Relay)

### `/translate` (r3 신규)

**HTTP로 받은 텍스트를 번역하고, HTTP로 번역문을 반환하는 범용 API**. Discord를 경유하지 않습니다.

- **POST** `/translate`

- **Request (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""` (미지정/auto/빈 값은 내부에서 자동 판별)
  
  - `target`: 기본값은 `.env`의 `DEFAULT_REPLY_LANG` (예: `"ja"`)

- **Response (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **예: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **예: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### 반환 값의 약속

- `ok`가 `true`일 때 `translated`에 번역문

- 실패 시 `{ "ok": false, "error": "<message>" }`를 반환 (HTTP 4xx/5xx)

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — 콘솔 이름과 수신처 (dm/channel, id, lang 등)를 등록

- `POST /send` — 지정된 콘솔로 텍스트 전송 (Discord 측으로 배송)

- `POST /send_image` — 이미지 OCR → 번역 → 인페인팅 → 전송

- `GET /stats` — 실행 상태 및 바인딩 목록> `/translate`는 **HTTP 클라이언트에 직접 응답**하기 때문에 VS Code와 같은 외부 도구와의 연동에 최적입니다. 기존의 Discord 경유 흐름은 `/bind`와 `/send`를 사용합니다.

---

## 로그 (JSONL)

- 기본: `log/messages.jsonl`. `.env`의 `IMTBD_JSONL_PATH`로 저장 위치를 변경할 수 있습니다.  
- UI는 이 파일을 tail하여 화면에 표시합니다. UNC 공유를 통해서도 열람 가능합니다.

---

## VS Code 래퍼 연동 예시

- 확장 측 설정: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- 선택 → **일본어로 선택 내용 교체** (예: `Ctrl+Alt+K`)로 **즉시 교체**

- 클립보드 번역 (`Ctrl+Alt+J`), 호버 번역 등은 확장 측의 설정에 따릅니다.

---

## 자주 묻는 질문 (FAQ)

**Q: Windows의 UNC 경로는 어떻게 작성하나요?**  
A: `.env`에서는 `\\raspberrypi\IMTB-D\messages.jsonl`을 **백슬래시 2개**로 작성합니다.  
   `.env` 내의 이스케이프 상, 실제로는 `\\\\raspberrypi\\IMTB-D\\messages.jsonl`로 작성하는 것이 안전합니다.

**Q: `fetch failed`가 발생합니다.**  
A: `localhost`가 IPv6로 해결되어 연결할 수 없는 경우가 있습니다. **`127.0.0.1`**로 시도해 보세요. 원격의 경우 `<server-ip>`를 사용합니다.

**Q: Permission denied (`console_routes.json` 쓰기)**  
A: 에디터가 파일을 열어둔 상태(배타적)이거나, Windows의 Controlled Folder Access가 원인일 수 있습니다. 저장 위치를 사용자 디렉토리로 변경하거나, 에디터를 닫고 다시 실행하세요.

---

## 개발/운영 팁

- **r3의 핫 리로드** (저장 시 재시작)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **상주화 (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Git 운영**
  
  - `/translate` 구현・README・CHANGELOG를 커밋
  
  - `.env`는 커밋하지 않음 (`.env.example` 제공)
  
  - `.vscode/`는 원칙적으로 ignore. 공유하고 싶다면 `extensions.json`/`tasks.json` 등, 비밀이 없는 최소한의 것만

---

## 라이센스

MIT 라이센스