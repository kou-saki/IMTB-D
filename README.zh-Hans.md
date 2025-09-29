## Discord 的互动多语言翻译机器人 (IMTB-D)

这是一个可以将 Discord 消息翻译成“喜欢的语言”并进行读写的 **翻译中继 Bot（Relay）**，配合 **桌面 UI（Tkinter）** 和可以在终端使用的 **Console** 的工具。  
翻译日志可以以 **JSONL** 格式保存，并且可以指定 UNC 共享路径（例如: `\\raspberrypi\IMTB-D\messages.jsonl`）。

- **Relay**: Discord Bot 和本地 HTTP API（`/bind`, `/send`, `/send_image`, `/stats`）

- **Relay r3 追加**: **`/translate`**（接收文本并通过 HTTP 返回翻译的通用 API）

- **UI**: .env 编辑、目标的注册与发送、日志查看、**文件翻译（实时预览）**、在本地时自动启动 Relay

- **Console**: 从终端进行绑定和发送。日志的 tail 显示

> 需要的东西：**Discord Bot Token** 和 **OpenAI API Key**（即使不直接调用 OpenAI 的配置也可以）

---

## 目录

- [构成](#%E6%A7%8B%E6%88%90)

- [要件](#%E8%A6%81%E4%BB%B6)

- [.env（最小例）](#env%E6%9C%80%E5%B0%8F%E4%BE%8B)

- [使用方法](#%E4%BD%BF%E7%94%A8%E6%96%B9)
  
  - [A. 本地使用 UI + Relay](#a-%E6%9C%AC%E5%9C%B0%E4%BD%BF%E7%94%A8-ui--relay)
  
  - [B. 连接远程 Relay](#b-%E8%BF%9E%E6%8E%A5%E8%BF%9C%E7%A8%8B-relay)
  
  - [C. Console（终端）](#c-console%E7%AB%99%E7%82%B9)

- [API（Relay）](#apirelay)
  
  - [/translate（r3 新规）](#translater3-%E6%96%B0%E8%A6%8F)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [日志（JSONL）](#%E6%97%A5%E5%BF%97jsonl)

- [VS Code 包装器集成示例](#vs-code-%E5%8C%85%E8%A3%85%E5%99%A8%E9%9B%86%E6%88%90%E7%A4%BA)

- [常见问题](#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98)

- [开发/运用提示](#%E5%BC%80%E5%8F%91%E8%BF%90%E7%94%A8tips)

- [许可证](#%E8%AE%B8%E5%8F%AF%E8%AF%81)

---

## 构成（主要文件）

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # 桌面 UI（Tkinter）
IMTB-D_console.py    # 终端用控制台
console_routes.json      # 目标的保存（UI 写入）
log/messages.jsonl       # 翻译日志（JSON Lines）
```

---

## 要件

- 下载主要文件
- Python 3.10+（支持 Tkinter 的环境）
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env（最小例）

在此仓库根目录下创建 `.env` 文件。

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Relay 的基础 URL（在 UI 本地运行时推荐使用 127.0.0.1）
IMTBD_API_BASE=http://127.0.0.1:8765

# Relay 绑定（监听）设置（未设置则默认: 127.0.0.1:8765）
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# （可选）翻译日志保存路径
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# （可选）翻译相关
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> 在 Linux/mac 使用 UNC 时，事先挂载并指定常规路径是更可靠的。※IMTBD_JSONL_PATH 是 **区分大小写**（Linux）

---

## 使用方法

### A. 本地使用 UI + Relay（最短）

```bash
python IMTB-D_ui.py
```

- `IMTBD_API_BASE` 为 `http://127.0.0.1:8765` 或 `localhost` 时，  
  UI 会 **自动辅助启动 Relay**（启动后显示“API ready”）。
  
  ![setup.png](docs/images/setup.png)
  
  在“Setup”标签中编辑 `.env` 并 **保存 .env**。

- 在“Destinations”标签中选择目标（DM/Channel） **绑定** → 输入文本 → **发送**。
  
  ![destinations.png](docs/images/destinations.png)

- 下方的日志会反映发送和接收情况。
  
  - 在选择目标（DM/Channel）状态下，点击“Open Window”→打开单独聊天窗口。
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - 文本翻译
    
    - 在窗口最下方的框中输入文本，按 send 或 Enter 发送。
    
    - 如果需要输入多行，可以使用 Ctrl+Enter 换行。
  
  - 图像翻译（Inpaint）
    
    - 通过拖放图片进行图像翻译。
    
    - 目前效果不是很好，但可以作为参考。
      
      翻译前
      
      ![origin.png](docs/images/origin.png)
      
      翻译后
      
      ![translated.png](docs/images/translated.png)

### B. 连接远程 Relay（例如：Raspberry Pi）

- 在服务器（如 Pi）上启动 `IMTB-D_relay.py`，
- 在 UI 侧的 `.env` 中将 `IMTBD_API_BASE` 设置为 `http://<server-ip>:8765`。  
- 在这种情况下，UI 的启动/停止功能将被禁用，并作为 **远程模式** 运行。

### C. Console（终端）

```bash
# 发送到频道
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# 发送到 DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# 直接在标准输入中输入将会发送（日志为 tail 显示）。
```

---

## API（Relay）

### `/translate`（r3 新规）

**接收 HTTP 文本并翻译，通过 HTTP 返回翻译的通用 API**。不经过 Discord。

- **POST** `/translate`

- **请求 (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""`（未指定/auto/空时内部自动判定）
  
  - `target`: 默认为 `.env` 中的 `DEFAULT_REPLY_LANG`（例如: `"ja"`）

- **响应 (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **示例: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **示例: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### 返回值的约定

- 当 `ok` 为 `true` 时，`translated` 中包含翻译文本

- 失败时返回 `{ "ok": false, "error": "<message>" }`（HTTP 4xx/5xx）

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — 注册控制台名称和目标（dm/channel, id, lang 等）

- `POST /send` — 向指定控制台发送文本（配送到 Discord 端）

- `POST /send_image` — 图像 OCR → 翻译 → Inpaint → 发送

- `GET /stats` — 启动状态和绑定列表> `/translate` 是 **直接回复 HTTP 客户端** 的最佳选择，适合与 VS Code 等外部工具的集成。传统的 Discord 流程使用 `/bind` 和 `/send`。

---

## 日志（JSONL）

- 默认: `log/messages.jsonl`。可以通过 `.env` 中的 `IMTBD_JSONL_PATH` 更改保存路径。  
- UI 会对该文件进行尾部跟踪并显示在屏幕上。即使通过 UNC 共享也可以查看。

---

## VS Code 包装器集成示例

- 扩展侧设置：`mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- 选择 → **用日语替换选择**（例如: `Ctrl+Alt+K`）进行**就地替换**

- 剪贴板翻译（`Ctrl+Alt+J`）、悬停翻译等遵循扩展侧的设置

---

## 常见问题（FAQ）

**Q: Windows 的 UNC 路径怎么写？**  
A: 在 `.env` 中使用 `\\raspberrypi\IMTB-D\messages.jsonl` **用两个反斜杠** 表示。  
   由于 `.env` 内的转义，实际写法最好是 `\\\\raspberrypi\\IMTB-D\\messages.jsonl`。

**Q: 出现 `fetch failed`**  
A: `localhost` 可能解析为 IPv6 而无法连接。请尝试使用 **`127.0.0.1`**。如果是远程，请使用 `<server-ip>`。

**Q: Permission denied（`console_routes.json` 写入）**  
A: 编辑器可能仍然打开文件（独占）或 Windows 的受控文件夹访问可能是原因。可以更改保存路径到用户目录，或关闭编辑器后重新执行。

---

## 开发/运维提示

- **r3 的热重载**（保存时重启）
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **常驻化（Linux, systemd）**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Git 运用**
  
  - 提交 `/translate` 实现、README 和 CHANGELOG
  
  - 不提交 `.env`（提供 `.env.example`）
  
  - 原则上忽略 `.vscode/`。如果需要共享，仅共享 `extensions.json`/`tasks.json` 等没有机密的最小部分

---

## 许可证

MIT 许可证