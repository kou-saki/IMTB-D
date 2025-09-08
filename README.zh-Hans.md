# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Discord 的消息可以翻译成“喜欢的语言”进行读写的 **翻译中继 Bot（Relay）**，以及可以从手边操作的 **桌面 UI（Tkinter）** 和可以从终端使用的 **Console** 的工具。(截至2025/09/08支持的语言：en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th) 翻译日志可以以 **JSONL** 格式保存，并且可以指定 UNC 共享路径（例如： `\\raspberrypi\IMTB-D\messages.jsonl`）。

- **Relay**: Discord Bot 和本地 HTTP API（`/bind`, `/send`, `/send_image`, `/stats`）。
- **UI**: .env 编辑、目标的注册与发送、日志查看、**文件翻译（实时预览）**、本地时自动启动 Relay。
- **Console**: 从终端进行绑定和发送。日志的 tail 显示。

> 所需内容：**Discord Bot Token** 和 **OpenAI API Key**。

---

## 结构（主要文件）

```
IMTB-D_relay.py      # Discord Bot + HTTP API
IMTB-D_ui.py         # 桌面 UI（Tkinter）
IMTB-D_console.py    # 终端用控制台
console_routes.json      # 目标的保存（UI 写入）
log/messages.jsonl       # 翻译日志（JSON Lines）
```

---

## 要求

- Python 3.10+（支持 Tkinter 的环境）
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env（最小示例）

在此仓库根目录下创建 `.env` 文件。

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# 本地使用时建议使用 localhost（UI 会自动启动 Relay）
IMTBD_API_BASE=http://127.0.0.1:8765

# （可选）日志的保存位置。Windows 使用 UNC，Linux/mac 使用常规路径即可
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# （可选）翻译设置
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> 在 Linux/mac 上使用 UNC 时，建议事先挂载并使用常规路径指定。※IMTBD_JSONL_PATH 是 **区分大小写**（Linux）

---

## 使用方法

### A. 本地使用 UI + Relay（最简）

```bash
python IMTB-D_ui.py
```

- 如果 `IMTBD_API_BASE` 为 `http://127.0.0.1:8765` 或 `localhost`，  
  UI 会 **自动辅助启动 Relay**（启动后显示“API ready”）。
  
  ![setup.png](docs/images/setup.png)
  
  在“Setup”标签中编辑 `.env` 并 **保存 .env**。

- 在“Destinations”标签中选择目标（DM/Channel）并 **绑定** → 输入文本 → **发送**。
  
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
- UI 侧的 `.env` 中将 `IMTBD_API_BASE` 设置为 `http://<server-ip>:8765`。  
- 在这种情况下，UI 的启动/停止功能将被禁用，并以 **远程模式** 运行。

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

- `POST /bind` — 注册控制台名称和目标（dm/channel, id, lang）  
- `POST /send` — 向指定控制台发送文本（`lang` 可临时覆盖）  
- `POST /send_image` — 图像的 OCR → 翻译 → Inpaint & 绘制 → 发送  
- `GET  /stats` — 启动状态和绑定列表

---

## 日志（JSONL）

- 默认： `log/messages.jsonl`。可以通过 `.env` 中的 `IMTBD_JSONL_PATH` 更改保存位置。  
- UI 会 tail 此文件并在屏幕上显示。也可以通过 UNC 共享查看。

---

## 常见问题（FAQ）

**问：Windows 的 UNC 路径该怎么写？**  
答：在 `.env` 中使用 `\\raspberrypi\IMTB-D\messages.jsonl`，需使用 **两个反斜杠**。  
   在 `.env` 中的转义上，实际应写为 `\\\\raspberrypi\\IMTB-D\\messages.jsonl` 更为稳妥。

---

## 许可证

MIT 许可证