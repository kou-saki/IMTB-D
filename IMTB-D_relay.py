import os, sys, asyncio, threading, json, re, base64, io, tempfile, uuid
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw

import discord
from discord import Intents, DMChannel, TextChannel
from dotenv import load_dotenv
from aiohttp import web

from openai import OpenAI

import signal
import atexit

# ===== paths / .env =====
# このスクリプトが置かれたディレクトリを基準に .env を読む（CWDに依存しない）
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH   = SCRIPT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # フォールバック: もしカレントに置いている運用なら従来の挙動も許容
    load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL      = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PREFERRED_LANG     = os.getenv("PREFERRED_LANG", "ja")
TARGET_CHANNEL_ID  = int(os.getenv("TARGET_CHANNEL_ID", "0"))
DEFAULT_REPLY_LANG = os.getenv("DEFAULT_REPLY_LANG", "en")
if not DISCORD_BOT_TOKEN or not OPENAI_API_KEY:
    print("Please set DISCORD_BOT_TOKEN and OPENAI_API_KEY in .env"); sys.exit(1)

client_oa = OpenAI(api_key=OPENAI_API_KEY)

# ===== JSONL logger =====
LOG_DIR = SCRIPT_DIR / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)
JSONL_PATH = LOG_DIR / "messages.jsonl"

def append_jsonl(record: dict):
    try:
        with JSONL_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[LOG] append_jsonl failed: {e}")

# ===== Discord intents =====
intents = Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# ===== Lang detect / translate =====
LANG_DETECT_SYS = "Return ONLY ISO 639-1 language code like 'en','ja','ko'. No extra text."
TRANSLATE_SYS   = ("You are a precise translator. Preserve meaning, tone, mentions, URLs, emojis; "
                   "keep formatting & code blocks. Output ONLY the translation.")

@lru_cache(maxsize=1024)
def detect_lang_cached(sample: str) -> str:
    try:
        r = client_oa.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role":"system","content":LANG_DETECT_SYS},
                      {"role":"user","content":sample[:1000]}],
            temperature=0
        )
        code = r.choices[0].message.content.strip().lower()
        return code.split()[0].strip(".,:;") if len(code) > 5 else code
    except Exception:
        return "en"

def translate_text(text: str, target_lang: str, source_lang: str|None=None) -> str:
    try:
        prompt = f"Translate this into '{target_lang}'."
        if source_lang: prompt += f" Source language hint: '{source_lang}'."
        prompt += "\n\nText:\n" + text
        r = client_oa.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role":"system","content":TRANSLATE_SYS},
                      {"role":"user","content":prompt}],
            temperature=0
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return text

# ===== Bot =====
class IMTBD_Relay(discord.Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        self.last_lang_per_channel: dict[int,str] = defaultdict(lambda: DEFAULT_REPLY_LANG)
        self.stdin_queue: asyncio.Queue[str] = asyncio.Queue()
        # console名 → {"type":"dm","user_id":..., "lang":"en"} or {"type":"channel","channel_id":..., "lang":"en"}
        self.console_routes: dict[str,dict] = {}

        # --- metrics ---
        self.metrics = {
            "ready": False,
            "session_id": "",
            "api_host": "127.0.0.1",
            "api_port": 8765,       # 実際にバインドしたポートで更新
            "bindings": 0,
            "queue": 0,
            "last_error": ""
        }
        
    async def setup_hook(self):
        # 標準入力（互換）
        def read_stdin(loop: asyncio.AbstractEventLoop, q: asyncio.Queue):
            for line in sys.stdin:
                asyncio.run_coroutine_threadsafe(q.put(line.rstrip("\n")), loop)
        threading.Thread(target=read_stdin, args=(asyncio.get_running_loop(), self.stdin_queue), daemon=True).start()
        self.loop.create_task(self._stdin_pump())

        # ローカルHTTP API
        await self._start_local_api()

    async def _start_local_api(self):
        app = web.Application()

        async def bind(request: web.Request):
            data = await request.json()
            name = data.get("console")
            if not name:
                return web.json_response({"ok": False, "error": "console required"}, status=400)
            self.console_routes[name] = {k:v for k,v in data.items() if k!="console"}
            print(f"[BIND] console={name} -> {self.console_routes[name]}")
            self.metrics["bindings"] = len(self.console_routes)
            append_jsonl({"ts": datetime.now(timezone.utc).isoformat(),
                          "direction":"event","event":"bind",
                          "route": self.console_routes[name] | {"console": name}})
            return web.json_response({"ok": True})

        async def send_image(request: web.Request):
            """
            JSON: {console, path?, filename?, b64?, lang?}
            1) OCR(bbox) with gpt-4o
            2) translate lines
            3) make mask & inpaint
            4) draw translated text
            5) post image to DM/Channel
            """
            data = await request.json()
            name = data.get("console") or ""
            img_path = data.get("path") or ""
            filename = (data.get("filename") or "image.png").strip()
            b64_in = data.get("b64")
            target_lang = (data.get("lang") or DEFAULT_REPLY_LANG).strip()
            if not name:
                return web.json_response({"ok": False, "error":"console required"}, status=400)
            route = self.console_routes.get(name)
            if not route:
                return web.json_response({"ok": False, "error":"console not bound"}, status=400)

            try:

                # ---- 0) 入力画像の実体を用意（b64優先）
                if b64_in:
                    tmp = Path(tempfile.gettempdir()) / f"IMTB-D_{uuid.uuid4().hex}{(Path(filename).suffix or '.png')}"
                    tmp.write_bytes(base64.b64decode(b64_in))
                    img_path = str(tmp)
                if not img_path or not Path(img_path).exists():
                    return web.json_response({"ok": False, "error": f"image not found: {img_path}"}, status=400)

                # ---- 1) OCR with bounding boxes
                b64img = base64.b64encode(Path(img_path).read_bytes()).decode("utf-8")
                prompt = (
                    "Extract visible textual regions with bounding boxes.\n"
                    "Return pure JSON list of objects: "
                    "[{\"text\":\"...\",\"bbox\":[x,y,w,h]}]. "
                    "Coordinates in pixels relative to original image. No extra text."
                )
                r = client_oa.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role":"user","content":[
                            {"type":"text","text":prompt},
                            {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64img}"}}
                        ]}
                    ],
                    temperature=0,
                )
                import json as _json
                raw = r.choices[0].message.content.strip()
                # 最後の JSON 配列ブロックを抽出（自己防衛）
                m = re.search(r"\[.*\]", raw, re.S)
                boxes = _json.loads(m.group(0) if m else raw)
                if not isinstance(boxes, list):
                    boxes = []
                # ---- 2) Translate
                lines = "\n".join(o.get("text","") for o in boxes)
                tr = client_oa.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role":"system","content":"Output ONLY the translation, same line breaks."},
                        {"role":"user","content":f"Translate into '{target_lang}'.\n\n{lines}"}
                    ],
                    temperature=0
                ).choices[0].message.content.split("\n")
                for i,o in enumerate(boxes):
                    o["translated"] = tr[i] if i < len(tr) else o.get("text","")

                # ---- 3) Mask & Inpaint
                im = Image.open(img_path).convert("RGBA")
                mask = Image.new("RGBA", im.size, (0,0,0,0))
                draw = ImageDraw.Draw(mask)
                for o in boxes:
                    x,y,w,h = o["bbox"]; draw.rectangle([x,y,x+w,y+h], fill=(0,0,0,255))
                buf_img, buf_mask = io.BytesIO(), io.BytesIO()
                im.save(buf_img, format="PNG"); mask.save(buf_mask, format="PNG")
                buf_img.seek(0); buf_mask.seek(0)
                # ★ OpenAI Images API は mimetype 推定にファイル名を使う。
                #   BytesIO のままだと application/octet-stream になるので拡張子付き名を付与。
                setattr(buf_img, "name", "image.png")
                setattr(buf_mask, "name", "mask.png")
                # 画像編集（インペイント）。戻り画像のサイズはモデル依存のため、
                # 後段描画でスケール補正する。
                # OpenAI Images API は固定サイズのみ対応
                # サポートされる値: 1024x1024, 1024x1536, 1536x1024, auto
                w, h = im.width, im.height
                if h >= w*1.3:
                    size_str = "1024x1536"
                elif w >= h*1.3:
                    size_str = "1536x1024"
                else:
                    size_str = "1024x1024"

                try:
                    edited = client_oa.images.edit(
                        model="gpt-image-1",
                        image=buf_img,
                        mask=buf_mask,
                        prompt="Remove the masked text and naturally restore the background.",
                        size=size_str,
                    )
                    # SDKのバージョンにより data[0] は b64_json か url を返す
                    painted_bytes = None
                    d0 = edited.data[0]
                    if getattr(d0, "b64_json", None):
                        import base64 as _b64
                        painted_bytes = _b64.b64decode(d0.b64_json)
                    elif getattr(d0, "url", None):
                        from urllib.request import urlopen
                        with urlopen(d0.url, timeout=60) as resp:
                            painted_bytes = resp.read()
                    else:
                        raise RuntimeError("Images API returned neither b64_json nor url")
                    painted = Image.open(io.BytesIO(painted_bytes)).convert("RGBA")
                    used_inpaint = True
                except Exception as e_inpaint:
                    # 403 などで画像編集が使えない場合は上描き方式にフォールバック
                    msg = str(e_inpaint)
                    if "unknown_parameter" in msg or "must be verified" in msg or "403" in msg:
                        painted = im.copy()   # 元画像をそのまま使って上描き
                        used_inpaint = False
                    else:
                        raise

                # ---- 4) Draw translated text back
                # 座標スケール補正（インペイント結果と元画像のサイズ差を吸収）
                sx = painted.width  / im.width
                sy = painted.height / im.height
                draw2 = ImageDraw.Draw(painted)
                for o in boxes:
                    try:
                        x,y,w,h = o["bbox"]
                    except Exception:
                        continue
                    X, Y = int(x*sx), int(y*sy)
                    W, H = int(w*sx), int(h*sy)
                    if not used_inpaint:
                        # フォールバック時：背景を薄く白で塗ってから文字を描く
                        draw2.rectangle([X, Y, X+W, Y+H], fill=(255,255,255,220))
                    # 簡易レイアウト（後で改良可）
                    draw2.text((X, Y), str(o.get("translated","")), fill=(0,0,0,255))

                out_path = Path(img_path).with_suffix(f".{target_lang}.png")
                painted.save(out_path, format="PNG")

                # ---- 5) Post to Discord
                if route.get("type") == "dm":
                    user = await self.fetch_user(int(route["user_id"]))
                    dm = await user.create_dm()
                    await dm.send(file=discord.File(str(out_path)))
                else:
                    ch = self.get_channel(int(route["channel_id"])) or await self.fetch_channel(int(route["channel_id"]))
                    await ch.send(file=discord.File(str(out_path)))

                append_jsonl({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "direction": "outbound",
                    "channel_id": route.get("channel_id"),
                    "to_user_id": route.get("user_id"),
                    "to_lang": target_lang,
                    "original": f"[image]{Path(img_path).name}",
                    "translated": f"[image]{out_path.name}",
                    "console": name,
                })
            except Exception as e:
                self.metrics["last_error"] = str(e)
                return web.json_response({"ok": False, "error": str(e)}, status=500)

            return web.json_response({"ok": True})


        async def send(request: web.Request):
            data = await request.json()
            name = data.get("console")
            text = (data.get("text") or "").strip()
            if not name or not text:
                return web.json_response({"ok": False, "error": "console/text required"}, status=400)
            route = self.console_routes.get(name)
            if not route:
                return web.json_response({"ok": False, "error": "console not bound"}, status=400)

            # ★ 追加：個別送信時の言語上書き（auto/空は無視）
            override_lang = (data.get("lang") or "").strip().lower()
            if override_lang in ("", "auto"):
                override_lang = None

            try:
                if route.get("type") == "dm":
                    to_lang = override_lang or route.get("lang") or DEFAULT_REPLY_LANG
                    user_id = int(route["user_id"])
                    translated = translate_text(text, to_lang)
                    user = await self.fetch_user(user_id)
                    dm = await user.create_dm()
                    await dm.send(translated)
                    print(f"[API SEND DM] {name} -> {user} ({to_lang}) : {translated[:120]}{'...' if len(translated)>120 else ''}")
                    append_jsonl({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "direction": "outbound_dm",
                        "to_user_id": user_id,
                        "user_name": str(user),
                        "to_lang": to_lang,
                        "original": text,
                        "translated": translated,
                        "console": name,
                    })
                elif route.get("type") == "channel":
                    channel_id = int(route["channel_id"])
                    to_lang = override_lang or route.get("lang") or self.last_lang_per_channel.get(channel_id, DEFAULT_REPLY_LANG)
                    translated = translate_text(text, to_lang)
                    ch = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
                    await ch.send(translated)
                    print(f"[API SEND CH] {name} -> #{getattr(ch,'name',channel_id)} ({to_lang}) : {translated[:120]}{'...' if len(translated)>120 else ''}")
                    append_jsonl({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "direction": "outbound",
                        "channel_id": channel_id,
                        "channel_name": getattr(ch, "name", None),
                        "to_lang": to_lang,
                        "original": text,
                        "translated": translated,
                        "console": name,
                    })
                else:
                    return web.json_response({"ok": False, "error": "unknown route type"}, status=400)
            except Exception as e:
                self.metrics["last_error"] = str(e)
                return web.json_response({"ok": False, "error": str(e)}, status=500)

            return web.json_response({"ok": True})

        async def stats(_req):
            snap = dict(self.metrics); snap["routes"] = self.console_routes
            return web.json_response({"ok": True, "stats": snap})

        app.add_routes([
            web.post("/bind", bind),
            web.post("/send", send),
            web.post("/send_image", send_image),
            web.get("/stats", stats)
        ])

        # ルート可視化（運用確認用）
        print("[API] routes:", [r.resource.canonical for r in app.router.routes()])

        runner = web.AppRunner(app); await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.metrics["api_port"])
        await site.start()
        print(f"[API] Local API started at http://{self.metrics['api_host']}:{self.metrics['api_port']}")
        append_jsonl({"ts": datetime.now(timezone.utc).isoformat(),
                      "direction":"event","event":"api_started",
                      "host": self.metrics["api_host"], "port": self.metrics["api_port"]})

    async def on_ready(self):
        self.metrics["ready"] = True
        try:
            self.metrics["session_id"] = getattr(getattr(self, "ws", None), "session_id", "") or ""
        except Exception:
            pass
        append_jsonl({"ts": datetime.now(timezone.utc).isoformat(),
                      "direction":"event","event":"ready",
                      "bot_id": self.user.id, "bot_name": str(self.user)})

    async def on_message(self, message: discord.Message):
        if message.author.bot: return
        if not message.content and not message.attachments: return
        channel = message.channel
        content = message.content or ""
        if message.attachments:
            content = (content + ("\n" if content else "") +
                       "\n".join(f"[attachment] {a.url}" for a in message.attachments)).strip()

        src = detect_lang_cached(content) if content else DEFAULT_REPLY_LANG
        if isinstance(channel, TextChannel):
            self.last_lang_per_channel[channel.id] = src

        translated = translate_text(content, PREFERRED_LANG, source_lang=src) if src != PREFERRED_LANG else content

        ch_name = f"#{channel.name}" if hasattr(channel, "name") else str(channel.id)
        print("\n" + "-"*60)
        print(f"[{ch_name}] {message.author.display_name} ({src})")
        print(content)
        print("  └▶ to", PREFERRED_LANG, "→")
        print(translated)
        print("-"*60)

        # ★ 受信ログ（DM/チャンネル）
        if isinstance(channel, DMChannel):
            append_jsonl({
                "ts": datetime.now(timezone.utc).isoformat(),
                "direction": "dm_inbound",
                "user_id": message.author.id,
                "user_name": message.author.display_name,
                "src_lang": src,
                "to_lang": PREFERRED_LANG,
                "original": message.content or "",
                "translated": translated,
            })
        elif isinstance(channel, TextChannel):
            append_jsonl({
                "ts": datetime.now(timezone.utc).isoformat(),
                "direction": "inbound",
                "channel_id": channel.id,
                "channel_name": channel.name,
                "author_id": message.author.id,
                "author_name": message.author.display_name,
                "src_lang": src,
                "to_lang": PREFERRED_LANG,
                "original": message.content or "",
                "translated": translated,
            })

    async def _stdin_pump(self):
        # 互換: /to /say を残す（使わなくてもOK）
        await self.wait_until_ready()
        while not self.is_closed():
            line = (await self.stdin_queue.get()).strip()
            if not line: continue
            channel_id = TARGET_CHANNEL_ID
            if channel_id == 0:
                print("[WARN] TARGET_CHANNEL_ID is not set."); continue
            if line.startswith("/to "):
                parts = line.split(maxsplit=3)
                if len(parts) < 3:
                    print("Usage: /to <lang> <channel_id?> <text>"); continue
                target_lang = parts[1]
                if len(parts) >= 4 and parts[2].isdigit():
                    channel_id = int(parts[2]); text = parts[3]
                else:
                    text = line.split(maxsplit=2)[2]
            elif line.startswith("/say "):
                text = line[len("/say "):]
                target_lang = self.last_lang_per_channel.get(channel_id, DEFAULT_REPLY_LANG)
            else:
                text = line
                target_lang = self.last_lang_per_channel.get(channel_id, DEFAULT_REPLY_LANG)

            translated = translate_text(text, target_lang)
            ch = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
            await ch.send(translated)
            print(f"[SENT] #{getattr(ch,'name',channel_id)} ({target_lang}) : {translated[:80]}{'...' if len(translated)>80 else ''}")
            append_jsonl({
                "ts": datetime.now(timezone.utc).isoformat(),
                "direction": "outbound",
                "channel_id": channel_id,
                "channel_name": getattr(ch, "name", None),
                "to_lang": target_lang,
                "original": text,
                "translated": translated,
                "console": "stdin",
            })

def main():
    bot = IMTBD_Relay(intents=intents)
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()
