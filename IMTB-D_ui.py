# -*- coding: utf-8 -*-
import os, sys, json, time, threading, subprocess, queue
from pathlib import Path, PureWindowsPath
import socket
from dotenv import load_dotenv
load_dotenv(override=True)   # ← .env を最優先にする
import time as _time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import List, Callable, Optional
    
# ---- optional Drag&Drop ----
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False


try:
    import winsound
except Exception:
    winsound = None

# ---- パス & ファイル ----
BASE = Path(__file__).resolve().parent
# .env は IMTB-D_ui.py と同じ階層に置く（/home/username/IMTB-D-relay/.env）
ENV_PATH = BASE / ".env"
LOG_DIR = BASE / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)
def _to_path(p: str) -> Path:
    # Windows なら UNC を安全に解釈
    if os.name == "nt":
        return Path(PureWindowsPath(p))
    # Linux/mac はそのまま（UNC は不可なので要マウント）
    return Path(p)

# 1) env 最優先
_jsonl_env = os.environ.get("IMTBD_JSONL_PATH")
if _jsonl_env:
    JSONL_PATH = _to_path(_jsonl_env)
else:
    # 2) 既定の UNC or 3) ローカルにフォールバック
    UNC_DIR = _to_path(r"\\raspberrypi\IMTB-D")
    LOCAL_DIR = Path.home() / "IMTB-D_fallback"
    BASE_DIR = UNC_DIR if UNC_DIR.exists() else LOCAL_DIR
    JSONL_PATH = BASE_DIR / "messages.jsonl"

ROUTES_PATH = BASE / "console_routes.json"

# 起動時に安全に作成
try:
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
except OSError as e:
    # 最終フォールバック（UNCが死んでる・権限ない等）
    LOCAL_FALLBACK = Path.home() / "IMTB-D_fallback"
    JSONL_PATH = LOCAL_FALLBACK / "messages.jsonl"
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    
# ---- OpenAI / Translator settings ----
from openai import OpenAI
from urllib.parse import urlparse
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TARGET = os.getenv("PREFERRED_LANG", "ja")
OUTPUT_DIR     = os.getenv("OUTPUT_DIR", "").strip()


# 環境変数でAPI先を上書き可能（例: http://<PiのIP>:8765）
# 正規化：スキーム無しや空白を吸収
API_BASE = (os.environ.get("IMTBD_API_BASE", "http://127.0.0.1:8765") or "").strip()
if "://" not in API_BASE:
    API_BASE = "http://" + API_BASE
try:
    _host_for_mode = (urlparse(API_BASE).hostname or "").lower()
except Exception:
    _host_for_mode = ""
RELAY_PY = BASE / "IMTB-D_relay.py"   # ← 拡張子を明示

# ---- relay 起動補助（UIから自動起動＆監視）----
def _is_listening(host: str, port: int, timeout: float = 0.8) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def _ensure_relay_if_local(api_base: str) -> subprocess.Popen | None:
    """
    API_BASE が 127.0.0.1 / localhost を指していて、該当ポートに relay が居なければ
    UI 側で自動起動する。起動済みなら None を返す。
    """
    try:
        u = urlparse(api_base)
        host = (u.hostname or "127.0.0.1").lower()
        port = int(u.port or 8765)
    except Exception:
        host, port = "127.0.0.1", 8765

    # リモート運用（localhost 以外）は触らない
    if host not in ("127.0.0.1", "localhost"):
        return None
    if _is_listening(host, port):
        return None
    cmd = os.getenv("IMTBD_RELAY_CMD")
    if not cmd:
        cmd = f"{sys.executable} {RELAY_PY}"
    return subprocess.Popen(cmd, shell=True, cwd=str(BASE))


# ---- ユーティリティ ----
print("[IMTB-D] API_BASE (effective) =", repr(API_BASE))  # デバッグ表示（必要なら外してOK）
def load_env():
    data = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#"): continue
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
    return data

def save_env(d: dict):
    # 必要なキーだけ書く。既存は上書き／不在は残す
    cur = load_env()
    cur.update(d)
    lines = [f"{k}={v}" for k, v in cur.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

def http_post(path, payload, timeout=15):
    r = requests.post(API_BASE + path, json=payload, timeout=timeout)
    try:
        data = r.json()
    except Exception:
        r.raise_for_status()
        return {}
    if not r.ok or not data.get("ok", False):
        raise RuntimeError(data.get("error", f"HTTP {r.status_code}"))
    return data

def load_routes():
    if ROUTES_PATH.exists():
        try:
            return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_routes(data: dict):
    ROUTES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- ログフォロワ（messages.jsonl）----
class Tailer(threading.Thread):
    def __init__(self, cb):
        super().__init__(daemon=True)
        self.cb = cb
        self._stop = threading.Event()

    def run(self):
        # UNC/SMBでは同一ハンドルのEOF待機が更新を拾えないことがあるため、
        # statでサイズ監視し、差分だけ読み、3秒ごとに明示的にreopenする。
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            JSONL_PATH.touch(exist_ok=True)
        except Exception:
            pass

        f = None
        pos = 0
        last_reopen = 0.0
        buf = ""
        while not self._stop.is_set():
            try:
                size = JSONL_PATH.stat().st_size
            except Exception:
                time.sleep(0.5); continue

            now = time.time()
            if f is None or (now - last_reopen) > 3.0:
                try:
                    if f: f.close()
                    f = JSONL_PATH.open("r", encoding="utf-8", errors="replace")
                    f.seek(pos, 0)
                    last_reopen = now
                except Exception:
                    time.sleep(0.5); continue

            # ローテーション等で縮んだら最初から
            if size < pos:
                try:
                    f.close()
                except Exception:
                    pass
                try:
                    f = JSONL_PATH.open("r", encoding="utf-8", errors="replace")
                    pos = 0; buf = ""; last_reopen = now
                except Exception:
                    time.sleep(0.5); continue

            if size > pos:
                try:
                    f.seek(pos, 0)
                    chunk = f.read(size - pos)
                    pos = size
                except Exception:
                    time.sleep(0.3); continue
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if line.strip():
                        try:
                            self.cb(json.loads(line))
                        except Exception:
                            pass
            else:
                time.sleep(0.3)

    def stop(self):
        self._stop.set()

# ===================== File Transfer helpers =====================
TRANSLATE_SYS = (
    "You are a precise translator. Preserve meaning, tone, and structure. "
    "Keep existing Markdown/code fences, headings, links, tables, and inline code. "
    "DO NOT summarize or omit content. Output ONLY the translation."
)

def _approx_token_count(s: str) -> int:
    return max(1, int(len(s) / 3.5))

@dataclass
class _ChunkPlan:
    max_tokens: int = 3500
    overlap: int = 0

def _chunk_text(text: str, plan: _ChunkPlan) -> List[str]:
    paras = text.split("\n\n")
    chunks: List[str] = []
    cur: List[str] = []
    cur_tokens = 0
    for p in paras:
        ptoks = _approx_token_count(p) + 1
        if cur_tokens + ptoks > plan.max_tokens and cur:
            chunks.append("\n\n".join(cur))
            cur = [p]; cur_tokens = ptoks
        else:
            cur.append(p); cur_tokens += ptoks
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks

def _call_translate_stream(client: OpenAI, text: str, target_lang: str, on_delta: Callable[[str], None]):
    stream = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role":"system","content":TRANSLATE_SYS},
            {"role":"user","content":f"Translate this into '{target_lang}'.\n\n{text}"},
        ],
        temperature=0,
        stream=True,
    )
    # --- 既存: 逐次トークンを on_delta へ流す ---
    for ev in stream:
        try:
            delta = ev.choices[0].delta
            if delta and getattr(delta, "content", None):
                on_delta(delta.content)
        except Exception:
            pass

def _translate_long_text_stream(client: OpenAI, text: str, target_lang: str, plan: _ChunkPlan,
                                on_progress: Optional[Callable[[str], None]],
                                on_preview: Optional[Callable[[str], None]],
                                should_pause: Callable[[], bool] = lambda: False,
                                should_stop:  Callable[[], bool] = lambda: False) -> str:
    chunks = _chunk_text(text, plan)
    out_parts: List[str] = []
    for i, ch in enumerate(chunks, 1):
        # Stop 要求があれば即時終了
        if should_stop():
            raise RuntimeError("translation-stopped")
        if on_progress:
            on_progress(f"Translating chunk {i}/{len(chunks)}...")
        buf = []
        def _on_delta(s: str):
            buf.append(s)
            if on_preview: on_preview(s)
        for attempt in range(3):
            try:
                # ---- 一時停止（ポーリング）----
                while should_pause() and not should_stop():
                    _time.sleep(0.08)
                if should_stop():
                    raise RuntimeError("translation-stopped")
                _call_translate_stream(client, ch, target_lang, _on_delta)
                break  # 成功
            except Exception:
                if should_stop():
                    raise RuntimeError("translation-stopped")
                if attempt == 2:
                    raise
                _time.sleep(1.5*(attempt+1))
        out_parts.append("".join(buf))
        if on_preview: on_preview("\n\n")
    return "".join(out_parts)

def _ft_is_supported(p: Path) -> bool:
    return p.suffix.lower() in {".txt",".md",".rst",".html",".htm",".srt"}

def _ft_infer_encoding(_p: Path) -> str:  # 拡張余地あり
    return "utf-8"

def _ft_out_path(src: Path, lang: str) -> Path:
    base = src.with_suffix("")
    out_dir = Path(OUTPUT_DIR) if OUTPUT_DIR else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{base.name}.{lang}.md"

    

# ---- GUI ----
class App(TkinterDnD.Tk if DND_AVAILABLE else tk.Tk):
    def open_search_window(self):
        w = tk.Toplevel(self)
        w.title("Search Messages"); w.geometry("500x400")
        tk.Label(w, text="Keyword:").pack(anchor="w", padx=8, pady=(8, 2))
        v = tk.StringVar()
        e = tk.Entry(w, textvariable=v)
        e.pack(fill="x", padx=8, pady=(0, 6))

        result_box = tk.Text(w, wrap="word", height=15)
        result_box.pack(fill="both", expand=True, padx=8, pady=(0,8))
        result_box.tag_config("highlight", background="yellow", foreground="black")

        def _search():
            keyword = v.get().strip().lower()
            result_box.delete("1.0", "end")
            # 全ての既存 highlight タグを削除
            target_chat = None
            for n, r, txt in self._chat_windows:
                txt.tag_remove("highlight", "1.0", tk.END)
                if r == self.last_opened_route:  # 開いている履歴に限定してジャンプ
                    target_chat = txt

            if not keyword:
                result_box.insert("end", "(Empty keyword)")
                return
            try:
                with JSONL_PATH.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                            text = (rec.get("original", "") + rec.get("translated", "")).lower()
                            if keyword in text:
                                ts = rec.get("ts", "")
                                shown = f"[{ts}] {rec.get('original','')} -> {rec.get('translated','')}"
                                result_box.insert("end", shown + "\n")

                                # 1件目だけジャンプ（target_chatに対してのみ）
                                if target_chat:
                                    start = "1.0"
                                    pos = target_chat.search(keyword, start, stopindex=tk.END, nocase=True)
                                    if pos:
                                        end = f"{pos}+{len(keyword)}c"
                                        target_chat.tag_add("highlight", pos, end)
                                        target_chat.see(pos)
                                        break  # 最初の1ヒットだけジャンプ
                        except Exception:
                            continue
            except Exception as ex:
                result_box.insert("end", f"Search failed: {ex}")

        ttk.Button(w, text="Search", command=_search).pack(pady=(0, 8))

    def _load_message_history(self, route: dict, limit: int = 20, offset: int = 0) -> list:
        total_lines = sum(1 for _ in JSONL_PATH.open("r", encoding="utf-8"))
        if offset >= total_lines:
            return []

        if not JSONL_PATH.exists():
            return []
        try:
            with JSONL_PATH.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            matched = []
            for line in reversed(lines):  # 新しい順
                try:
                    rec = json.loads(line)
                    if self._match_route(rec, route) and rec.get("direction", "").startswith(("inbound", "outbound", "dm_")):
                        matched.append(rec)
                    if len(matched) >= limit + offset:
                        break
                except Exception:
                    continue
            return matched[offset:offset + limit]
        except Exception as e:
            print(f"[HISTORY] Load failed: {e}")
            return []

    def __init__(self):
        super().__init__()
        self.history_offset = {}  # {console_name: offset_int}
        self.history_limit = 20
        self.title("IMTB-D Relay UI")
        self.geometry("880x620")
        self.relay_proc = None
        self.routes = load_routes()
        self.log_queue = queue.Queue()
        self.bind_all("<Control-f>", lambda e: self.open_search_window())
        # 原文/訳文の2行表示フラグ（既定ON）
        self.dual_view = tk.BooleanVar(value=True)
        # リモートAPIかどうかを判定
        self.remote_mode = _host_for_mode not in ("127.0.0.1", "localhost")
        
        # File Transfer: OpenAI client（キーが無ければNoneのまま）
        self.ft_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        # File Transfer state vars
        self.ft_var_lang = tk.StringVar(value=DEFAULT_TARGET)
        self.ft_var_max = tk.IntVar(value=3500)
        # ---- Pause/Stop flags for File Transfer ----
        # Pause: set() の間は受信ループを待機、Stop: set() されたら即座に打ち切り
        self.ft_pause = threading.Event()
        self.ft_stop  = threading.Event()

        # --- 自動 relay 起動（ローカルの場合のみ）---
        #   - API_BASE が localhost/127.0.0.1 なら、未起動時に UI が起動・待機
        #   - 既に起動済み or リモート接続なら何もしない
        self.lbl_status_text = tk.StringVar(value="Status: idle")
        try:
            # 先に status ラベルを作る前に少し文言を反映したいので遅延せず処理
            p = _ensure_relay_if_local(API_BASE)
            self.relay_proc = p
            if p is not None:
                self.lbl_status_text.set("Status: starting relay...")
                # 軽いヘルスチェック（2秒以内に疎通が出れば running 扱い）
                self.after(800, self._check_api_ready)
            else:
                # p が None： (a) 既に起動済み か (b) リモート接続
                if self.remote_mode:
                    self.lbl_status_text.set(
                        f"Status: remote mode ready (API {API_BASE}, log {JSONL_PATH})"
                    )
                else:
                    self.lbl_status_text.set(
                        f"Status: local relay detected (log {JSONL_PATH})"
                    )
        except Exception:
            pass

        self._build_ui()
        self._start_tailer()
        self.after(200, self._drain_log_queue)

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # --- 設定タブ ---
        frm_cfg = ttk.Frame(nb); nb.add(frm_cfg, text="Setup")
        self.var_token = tk.StringVar(value=load_env().get("DISCORD_BOT_TOKEN",""))
        self.var_openai = tk.StringVar(value=load_env().get("OPENAI_API_KEY",""))
        self.var_pref   = tk.StringVar(value=load_env().get("PREFERRED_LANG","ja"))
        self.var_def    = tk.StringVar(value=load_env().get("DEFAULT_REPLY_LANG","en"))

        g = ttk.Frame(frm_cfg); g.pack(fill="x", padx=12, pady=8)
        ttk.Label(g, text="Discord Bot Token").grid(row=0, column=0, sticky="e"); tk.Entry(g, textvariable=self.var_token, width=70).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Label(g, text="OpenAI API Key").grid(row=1, column=0, sticky="e"); tk.Entry(g, textvariable=self.var_openai, width=70, show="•").grid(row=1, column=1, sticky="we", padx=6)
        ttk.Label(g, text="Preferred Lang (UI表示)").grid(row=2, column=0, sticky="e"); tk.Entry(g, textvariable=self.var_pref, width=10).grid(row=2, column=1, sticky="w", padx=6)
        ttk.Label(g, text="Default Reply Lang").grid(row=3, column=0, sticky="e"); tk.Entry(g, textvariable=self.var_def, width=10).grid(row=3, column=1, sticky="w", padx=6)

        btns = ttk.Frame(frm_cfg); btns.pack(fill="x", padx=12, pady=8)
        ttk.Button(btns, text="Save .env", command=self.on_save_env).pack(side="left")
        self.btn_start = ttk.Button(btns, text="Start Relay", command=self.on_start_relay)
        self.btn_start.pack(side="left", padx=8)
        self.btn_stop = ttk.Button(btns, text="Stop Relay", command=self.on_stop_relay)
        self.btn_stop.pack(side="left")
        ttk.Button(btns, text="Ping API", command=self.on_ping).pack(side="left", padx=8)
        ttk.Checkbutton(btns, text="Dual view (orig+trans)", variable=self.dual_view)\
            .pack(side="left", padx=8)

        self.lbl_status = ttk.Label(frm_cfg, textvariable=self.lbl_status_text)
        self.lbl_status.pack(anchor="w", padx=12, pady=4)

        # リモート時はローカル起動/停止を無効化
        if self.remote_mode:
            try:
                self.btn_start.state(["disabled"])
                self.btn_stop.state(["disabled"])
            except Exception:
                pass
            self.lbl_status_text.set(f"Status: remote mode (API {API_BASE}, log {JSONL_PATH})")


        # --- 宛先タブ（登録＆送信） ---
        frm_routes = ttk.Frame(nb); nb.add(frm_routes, text="Destinations")

        # 左：フォーム、右：ログ＆送信欄
        left = ttk.LabelFrame(frm_routes, text="Add / Bind"); left.pack(side="left", fill="y", padx=8, pady=8)
        right = ttk.LabelFrame(frm_routes, text="Chat"); right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self.var_console = tk.StringVar()
        self.var_type = tk.StringVar(value="dm")
        self.var_id = tk.StringVar()
        self.var_lang = tk.StringVar(value="en")

        ttk.Label(left, text="Name (unique)").grid(row=0, column=0, sticky="e"); tk.Entry(left, textvariable=self.var_console, width=22).grid(row=0, column=1, pady=2)
        ttk.Label(left, text="Type").grid(row=1, column=0, sticky="e")
        ttk.Radiobutton(left, text="DM (user_id)", value="dm", variable=self.var_type).grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(left, text="Channel (channel_id)", value="channel", variable=self.var_type).grid(row=2, column=1, sticky="w")
        ttk.Label(left, text="ID").grid(row=3, column=0, sticky="e"); tk.Entry(left, textvariable=self.var_id, width=22).grid(row=3, column=1, pady=2)
        ttk.Label(left, text="Send Lang").grid(row=4, column=0, sticky="e"); tk.Entry(left, textvariable=self.var_lang, width=10).grid(row=4, column=1, sticky="w")
        ttk.Button(left, text="Bind", command=self.on_bind).grid(row=5, column=1, sticky="we", pady=4)
        ttk.Button(left, text="Save Destinations", command=self.on_save_routes).grid(row=6, column=1, sticky="we")

        # 既存ルート一覧
        ttk.Label(left, text="Registered:").grid(row=7, column=0, sticky="ne", pady=(10,2))
        self.lst = tk.Listbox(left, height=12, width=28)
        self.lst.grid(row=7, column=1, sticky="we", pady=(10,2))
        self.refresh_listbox()

        # 右ペイン：先頭に選択中の説明 + Show All / Sound(Master) 切り替え、下にログと送信欄
        toprow = ttk.Frame(right); toprow.pack(fill="x")
        self.lbl_current = ttk.Label(toprow, text="No destination selected.")
        self.lbl_current.pack(side="left", anchor="w")
        self.var_show_all = tk.BooleanVar(value=False)
        ttk.Checkbutton(toprow, text="Show All", variable=self.var_show_all).pack(side="right")
        # ★ 全体の通知音スイッチ（マスター）
        self.var_sound_master = tk.BooleanVar(value=True)
        ttk.Checkbutton(toprow, text="🔔 Sound", variable=self.var_sound_master)\
            .pack(side="right", padx=(0,8))

        # 宛先ごとのサウンド設定を保持
        self.sound_prefs = {}  # {console_name: BoolVar}

        # ------------------------------------------------------------------
        # File Transfer タブ（既存の構成に追加：Pause / Stop ボタン）
        # ※ すでに File Transfer タブや top フレームがある場合は、
        #    その「Pick files…」ボタンの隣に以下の2ボタンを追加してください。
        # ------------------------------------------------------------------
        try:
            # 典型: File Transferタブの先頭行にある top フレームを探す
            # （実装差異がある場合は _build_ui の File Transfer 部分で
            #  下記2ボタンを明示的に配置してください）
            top = None
            for child in self.winfo_children():
                if isinstance(child, ttk.Notebook):
                    for i in range(child.index("end")):
                        tab = child.nametowidget(child.tabs()[i])
                        # タブ内に "Pick files…" ボタンがあれば同階層の top を使う
                        for w in tab.winfo_children():
                            if isinstance(w, ttk.Frame):
                                for x in w.winfo_children():
                                    if isinstance(x, ttk.Button) and x.cget("text").startswith("Pick files"):
                                        top = w
                                        break
                        if top: break
                    break
            if top is not None:
                def _on_pause_toggle():
                    if self.ft_pause.is_set():
                        self.ft_pause.clear(); btn_pause.config(text="Pause")
                    else:
                        self.ft_pause.set();   btn_pause.config(text="Resume")
                def _on_stop(): self.ft_stop.set()
                btn_stop  = ttk.Button(top, text="Stop",  command=_on_stop)
                btn_pause = ttk.Button(top, text="Pause", command=_on_pause_toggle)
                btn_stop.pack(side="right", padx=(6,6))
                btn_pause.pack(side="right", padx=(6,6))
        except Exception:
            pass
        self.txt_log = tk.Text(right, height=22, wrap="word")
        self.txt_log.pack(fill="both", expand=True, pady=6)
        send_row = ttk.Frame(right); send_row.pack(fill="x")
        self.var_send = tk.StringVar()
        tk.Entry(send_row, textvariable=self.var_send).pack(side="left", fill="x", expand=True)
        ttk.Button(send_row, text="Send", command=self.on_send).pack(side="left", padx=6)
        # 右下：ポップアウト
        pop = ttk.Frame(right); pop.pack(fill="x", pady=(4,0))
        ttk.Button(pop, text="Open Window", command=self.open_chat_window).pack(side="right")

        # --- Monitor タブ ---
        tab_mon = ttk.Frame(nb); nb.add(tab_mon, text="Monitor")
        self.txt_mon = tk.Text(tab_mon, height=18)
        self.txt_mon.pack(fill="both", expand=True, padx=8, pady=8)
        self.after(1000, self._poll_stats)
        self.lst.bind("<<ListboxSelect>>", self.on_select)

        # --- File Transfer タブ ---  ← ここに常設で追加（起動時に出る）
        tab_ft = ttk.Frame(nb); nb.add(tab_ft, text="File Transfer")
        top = ttk.Frame(tab_ft); top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Target language:").pack(side="left")
        ttk.Combobox(top, textvariable=self.ft_var_lang, width=8,
                     values=["ja","en","zh","ko","es","fr","de","it","pt","ru","id","vi","th"]).pack(side="left", padx=6)
        ttk.Label(top, text="Max tokens per chunk:").pack(side="left", padx=(12,2))
        tk.Entry(top, textvariable=self.ft_var_max, width=6).pack(side="left")
        # Controls (right side): Pick / Pause / Stop
        ttk.Button(top, text="Pick files…", command=self._ft_pick_files).pack(side="right")
        def _on_pause_toggle():
            if self.ft_pause.is_set():
                self.ft_pause.clear(); self.btn_ft_pause.config(text="Pause")
            else:
                self.ft_pause.set();   self.btn_ft_pause.config(text="Resume")
        self.btn_ft_pause = ttk.Button(top, text="Pause", command=_on_pause_toggle)
        self.btn_ft_pause.pack(side="right", padx=(6,0))
        ttk.Button(top, text="Stop", command=lambda: self.ft_stop.set()).pack(side="right", padx=(6,0))

        self.ft_preview = tk.Text(tab_ft, height=14, wrap="word")
        self.ft_preview.pack(fill="both", expand=True, padx=10, pady=(4,6))
        self.ft_preview.insert("end","Drop files here (or use Pick files)…\n")
        if DND_AVAILABLE:
            self.ft_preview.drop_target_register(DND_FILES)
            self.ft_preview.dnd_bind("<<Drop>>", self._ft_on_drop)
        else:
            self.ft_preview.insert("end","(Drag & drop addon not found; using file picker instead.)\n")

        self.ft_log = tk.Text(tab_ft, height=10, wrap="word")
        self.ft_log.pack(fill="both", expand=True, padx=10, pady=(0,10))

    # ---- 動作 ----
    def on_save_env(self):
        save_env({
            "DISCORD_BOT_TOKEN": self.var_token.get().strip(),
            "OPENAI_API_KEY": self.var_openai.get().strip(),
            "PREFERRED_LANG": self.var_pref.get().strip() or "ja",
            "DEFAULT_REPLY_LANG": self.var_def.get().strip() or "en",
        })
        messagebox.showinfo("Saved", f".env saved at:\n{ENV_PATH}")


    def on_start_relay(self):
        if self.remote_mode:
            messagebox.showinfo(
                "Remote mode",
                "Start/Stop はリモート運用では無効です。\n"
                "サーバ側で実行してください:\n"
                "  sudo systemctl restart IMTB-D_bot"
            )
            return
        if self.relay_proc and self.relay_proc.poll() is None:
            messagebox.showinfo("Running", "Relay already running."); return
        if not RELAY_PY.exists():
            messagebox.showerror("Not found", f"{RELAY_PY} not found."); return
        # 起動
        cmd = os.getenv("IMTBD_RELAY_CMD")
        if cmd:
            self.relay_proc = subprocess.Popen(cmd, shell=True, cwd=str(BASE))
        else:
            self.relay_proc = subprocess.Popen([sys.executable, str(RELAY_PY)], cwd=str(BASE))
        self.lbl_status_text.set("Status: starting...")
        # API起動待ちを軽くポーリング
        self.after(800, self._check_api_ready)

    def _check_api_ready(self):
        try:
            # /bindに空を投げてみる（エラーなら起きてる証拠）
            requests.post(API_BASE + "/bind", json={"console":"_ping"}, timeout=1)
            self.lbl_status_text.set("Status: relay running (API ready)")
        except Exception:
            # 起動中
            if self.relay_proc and self.relay_proc.poll() is None:
                self.after(800, self._check_api_ready)
            else:
                self.lbl_status_text.set("Status: relay exited")

    def on_stop_relay(self):
        if self.remote_mode:
            messagebox.showinfo(
                "Remote mode",
                "Start/Stop はリモート運用では無効です。\n"
                "サーバ側で実行してください:\n"
                "  sudo systemctl stop IMTB-D_bot"
            )
            return
        if self.relay_proc and self.relay_proc.poll() is None:
            self.relay_proc.terminate()
            self.lbl_status_text.set("Status: stopped")
        else:
            self.lbl_status_text.set("Status: not running")

    def on_ping(self):
        """ローカルAPIの疎通確認。/bind にダミー投げてみる"""
        try:
            r = requests.post(API_BASE + "/bind",
                              json={"console": "_ping_ui"},
                              timeout=3)
            ok = (r.status_code in (200, 400, 422))  # 起きていれば何か返る
            if ok:
                self.lbl_status.config(text="Status: API reachable")
                messagebox.showinfo("Ping", "API is reachable.")
            else:
                self.lbl_status.config(text=f"Status: API HTTP {r.status_code}")
                messagebox.showwarning("Ping", f"API responded HTTP {r.status_code}")
        except Exception as e:
            self.lbl_status.config(text="Status: API not reachable")
            messagebox.showerror("Ping failed", str(e))


    def on_bind(self):
        name = self.var_console.get().strip()
        if not name:
            messagebox.showwarning("Input", "Name is required."); return
        rid = self.var_id.get().strip()
        if not rid.isdigit():
            messagebox.showwarning("Input", "ID must be numeric."); return
        route = {"console": name, "type": self.var_type.get(), "lang": self.var_lang.get().strip() or "en"}
        if route["type"] == "dm":
            route["user_id"] = int(rid)
        else:
            route["channel_id"] = int(rid)

        try:
            http_post("/bind", route)
            # 保存しておく
            rts = load_routes(); rts[name] = {k:v for k,v in route.items() if k!="console"}
            save_routes(rts); self.routes = rts; self.refresh_listbox()
            messagebox.showinfo("OK", f"Bound: {name}")
        except Exception as e:
            messagebox.showerror("Bind failed", str(e))

    def on_save_routes(self):
        save_routes(self.routes)
        messagebox.showinfo("Saved", f"Saved to {ROUTES_PATH}")

    def on_select(self, _evt):
        sel = self._cur_sel()
        if not sel: return
        name, route = sel
        # サウンド設定が無ければ初期化
        if name not in self.sound_prefs:
            self.sound_prefs[name] = tk.BooleanVar(value=True)
        snd_chk = "🔔ON" if self.sound_prefs[name].get() else "🔕OFF"
        self.lbl_current.config(text=f"Selected: {name} → {route}  (Sound:{snd_chk})")
        # フォームへ反映
        self.var_console.set(name)
        self.var_type.set(route.get("type","dm"))
        self.var_lang.set(route.get("lang","en"))
        self.var_id.set(str(route.get("user_id") or route.get("channel_id") or ""))

        # チェックボックスで切り替え
        top = self.lbl_current.master
        for w in top.pack_slaves():
            if getattr(w, "_is_sound_pref", False):
                w.destroy()
        cb = ttk.Checkbutton(top, text="🔔 This", variable=self.sound_prefs[name])
        cb._is_sound_pref = True
        cb.pack(side="right")

    def _cur_sel(self):
        if not self.routes: return None
        idxs = self.lst.curselection()
        if not idxs: return None
        name = self.lst.get(idxs[0]).split(" ")[0]
        return name, self.routes.get(name)

    def refresh_listbox(self):
        self.routes = load_routes()
        self.lst.delete(0, tk.END)
        for name, route in self.routes.items():
            target = route.get("user_id") or route.get("channel_id")
            self.lst.insert(tk.END, f"{name}  [{route.get('type')}]  id={target} lang={route.get('lang')}")

    def on_send(self):
        sel = self._cur_sel()
        if not sel:
            messagebox.showwarning("Select", "Select a destination from the list."); return
        name, route = sel
        text = self.var_send.get().strip()
        if not text: return
        payload = {"console": name, "text": text}
        try:
            http_post("/send", payload, timeout=30)
            self.var_send.set("")
            # ローカルエコー（JSONLを待たず一旦表示）
            t = datetime.now().strftime("%H:%M:%S")
            self._append_log(f"[{t}] you → [{name}] ({route.get('lang')}) {text}")
        except Exception as e:
            messagebox.showerror("Send failed", str(e))

    # ---- ログ表示 ----
    def _start_tailer(self):
        def cb(rec): self.log_queue.put(rec)
        self.tailer = Tailer(cb); self.tailer.start()

    def _drain_log_queue(self):
        try:
            while True:
                rec = self.log_queue.get_nowait()
                self._maybe_show(rec)
        except queue.Empty:
            pass
        self.after(200, self._drain_log_queue)

    def _maybe_show(self, rec: dict):
        # --- Show All（全フィード）: イベント以外は全部流す ---
        if getattr(self, "var_show_all", None) and self.var_show_all.get():
            # NOTE: dm_outbound が正（outbound_dm ではない）
            if rec.get("direction") in ("inbound", "outbound", "dm_inbound", "dm_outbound"):
                label = rec.get("channel_name") or rec.get("user_name") or "unknown"
                self._render(rec, label=label)


        # メインペイン
        sel = self._cur_sel()
        if sel:
            name, route = sel
            if self._match_route(rec, route):
                self._render(rec, label=name)
        # ポップアウト窓へ配信（存在しない Text は除外）
        alive = []
        for item in getattr(self, "_chat_windows", []):
            nm, rt, txt = item
            try:
                # 既に閉じられていればスキップ
                if not txt.winfo_exists():
                    continue
                if self._match_route(rec, rt):
                    line = self._format_line(rec, label=nm)
                    txt.insert(tk.END, line + "\n")
                    txt.see(tk.END)
                alive.append(item)
            except tk.TclError:
                # 破棄済みウィジェット
                continue
        self._chat_windows = alive

        # サウンド通知
        try:
            if winsound and self.var_sound_master.get():
                sel = self._cur_sel()
                if sel:
                    name, route = sel
                    if self.sound_prefs.get(name, tk.BooleanVar(value=True)).get():
                        winsound.Beep(800, 120)
        except Exception:
            pass

    def _render(self, rec, label=""):
        # 共通フォーマットを使って1行または2行を出力
        name = rec.get("channel_name") or rec.get("user_name") or label
        line = self._format_line(rec, label=name)
        # 2行返る場合があるので分割して追加
        for ln in line.splitlines():
            self._append_log(ln)

    # ---- 追加：共通ヘルパ ----
    def _match_route(self, rec, route):
        if route.get("type") == "dm":
            pid = int(route["user_id"])
            if rec.get("direction","").startswith("dm_") or rec.get("direction","").endswith("_dm"):
                return rec.get("user_id")==pid or rec.get("to_user_id")==pid
            return False
        else:
            cid = int(route["channel_id"])
            return rec.get("channel_id")==cid

    def _format_line(self, rec, label=""):
        role = "you" if rec.get("direction") in ("outbound", "dm_outbound") else "them"
        src = (rec.get("src_lang") or "").strip()
        dst = (rec.get("to_lang") or "").strip()
        original = (rec.get("original") or "").strip()
        translated = (rec.get("translated") or "").strip()
        ts = rec.get("ts", "")
        try:
            tshow = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M:%S") if ts else ""
        except Exception:
            tshow = ""
        name = rec.get("channel_name") or rec.get("user_name") or label
        head = f"[{tshow}] {role} → [{name}] ({src+'→'+dst if src or dst else (dst or src)})"

        # Dual view: 原文と訳文を2行で表示（内容が同一の場合は1行）
        if self.dual_view.get() and original and translated and original != translated:
            return f"{head}  {original}\n   ↳ {translated}"
        # 1行表示（訳文がなければ原文）
        text = translated or original
        return f"{head}  {text}"

    # ---- 追加：ポップアウト ----
    def open_chat_window(self):
        # --- 日付ブロック挿入用ヘルパ
        def insert_with_date_blocks(records):
            prev_date = None
            for rec in reversed(records):  # 時系列順に表示
                ts = rec.get("ts", "")
                try:
                    date = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
                except Exception:
                    date = None
                if date and date != prev_date:
                    txt.insert(tk.END, f"--- {date.isoformat()} ---\n")
                    prev_date = date
                line = self._format_line(rec, label=name)
                txt.insert(tk.END, line + "\n")
        sel = self._cur_sel()
        if not sel:
            messagebox.showwarning("Select","Pick a destination first."); return
        name, route = sel
        w = tk.Toplevel(self); w.title(f"Chat - {name}"); w.geometry("520x520")
        self.last_opened_route = route  # ← これを追加
        ttk.Label(w, text=f"{name} → {route}").pack(anchor="w", padx=8, pady=4)
        
        # 宛先個別サウンド
        if name not in self.sound_prefs:
            self.sound_prefs[name] = tk.BooleanVar(value=True)
        ttk.Checkbutton(w, text="🔔 Sound for this chat", variable=self.sound_prefs[name]).pack(anchor="w", padx=8)
        
        # --- 送信言語選択 ---
        ctrl = ttk.Frame(w); ctrl.pack(fill="x", padx=8, pady=(0,4))
        ttk.Label(ctrl, text="Send Lang").pack(side="left")
        lang_choices = ["auto","en","ja","zh-Hans","zh-Hant","ko","es","fr","de","it","pt-BR","ru","id","vi","th"]
        var_lang = tk.StringVar(value=route.get("lang") or "en")
        cmb = ttk.Combobox(ctrl, width=8, textvariable=var_lang, values=lang_choices, state="readonly")
        cmb.pack(side="left", padx=6)

        # ===== レイアウト: 上=可変パネル(3段: Chat / Drop(固定) / Text(最小高さあり)), 下=固定ツールバー =====

        # 上側は PanedWindow(縦) で 3 段に分割
        center = ttk.Panedwindow(w, orient="vertical")
        center.pack(fill="both", expand=True, padx=8, pady=(4,4))

        # --- (1) チャットビュー（可変、最優先で縮む）
        chat_container = ttk.Frame(center)
        txt_frame = ttk.Frame(chat_container)
        txt_frame.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(txt_frame, orient="vertical")
        txt = tk.Text(txt_frame, wrap="word", yscrollcommand=sb.set)
        sb.config(command=txt.yview)
        txt.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        txt_frame.rowconfigure(0, weight=1)
        txt_frame.columnconfigure(0, weight=1)
        txt.tag_config("highlight", background="yellow", foreground="black")
        center.add(chat_container, weight=1)  # 上段(チャット)は可変で最優先に縮む
        
        # --- 履歴表示（最新20件）
        self.history_offset[name] = 0
        history = self._load_message_history(route, limit=self.history_limit)
        insert_with_date_blocks(history)
        self.history_offset[name] += self.history_limit

        # スクロールイベントで更に読み込む（上方向）
        def on_scroll_up(event):
            if event.delta > 0:  # 上スクロール
                off = self.history_offset.get(name, 0)
                more = self._load_message_history(route, limit=self.history_limit, offset=off)
                if more:
                    prev_date = None
                    for rec in reversed(more):
                        ts = rec.get("ts", "")
                        try:
                            date = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
                        except Exception:
                            date = None
                        if date and date != prev_date:
                            txt.insert("1.0", f"--- {date.isoformat()} ---\n")
                            prev_date = date
                        line = self._format_line(rec, label=name)
                        txt.insert("1.0", line + "\n")
                    self.history_offset[name] += self.history_limit
        txt.bind("<MouseWheel>", on_scroll_up)  # Windows/Linux
        txt.bind("<Button-4>", on_scroll_up)    # Linux alt
        txt.bind("<Button-5>", on_scroll_up)

        # --- (2) 画像 D&D 領域（高さ固定・常に可視）
        DROP_H_LINES = 6  # 既存「現状の高さ」に合わせて調整可
        img_box = ttk.LabelFrame(w, text="Image Translate (Inpaint)")
        # Paned の 2 段目として追加するため、専用コンテナを作る
        drop_container = ttk.Frame(center)
        img_box_inner = ttk.Frame(drop_container)
        img_box_inner.pack(fill="x", expand=False)
        img_box_inner.configure(padding=(0,0,0,0))
        img_box.pack_forget()  # 安全のため
        img_box = ttk.LabelFrame(img_box_inner, text="Image Translate (Inpaint)")
        img_box.pack(fill="x", expand=False)
        drop = tk.Text(img_box, height=DROP_H_LINES, wrap="word")
        drop.insert("end", "Drop images here (.png .jpg .jpeg .webp .gif)\n")
        drop.configure(state="disabled")
        drop.pack(fill="x", padx=6, pady=(6,6))
        # 2 段目に追加（固定高さ相当を sashpos で維持）
        center.add(drop_container, weight=0)

        # internal state
        pending_images: list[str] = []
        paused = {"v": False}

        def _img_add(paths: list[str]):
            nonlocal pending_images
            for p in paths:
                p = p.strip().strip("{}")
                if not p: continue
                if not Path(p).exists(): continue
                if Path(p).suffix.lower() not in (".png",".jpg",".jpeg",".webp",".gif"):
                    continue
                pending_images.append(p)
            _refresh_drop()

        def _refresh_drop():
            drop.configure(state="normal"); drop.delete("1.0","end")
            if pending_images:
                drop.insert("end", "\n".join(Path(p).name for p in pending_images) + "\n")
            else:
                drop.insert("end","Drop images here (.png .jpg .jpeg .webp .gif)\n")
            drop.configure(state="disabled")

        def _split_dnd_paths(dnd: str) -> list[str]:
            items, buf, in_brace = [], "", False
            for ch in dnd:
                if ch == "{": in_brace=True; buf=""
                elif ch == "}": in_brace=False; items.append(buf)
                elif ch == " " and not in_brace:
                    if buf: items.append(buf); buf=""
                else: buf += ch
            if buf: items.append(buf)
            return items

        def _pick_files():
            paths = filedialog.askopenfilenames(filetypes=[
                ("Images","*.png *.jpg *.jpeg *.webp *.gif"),
                ("All files","*.*"),
            ])
            if paths: _img_add(list(paths))
        # pick ボタンは下部固定ツールバーに移動するため、ここではコマンドのみ定義

        if DND_AVAILABLE:
            drop.drop_target_register(DND_FILES)
            drop.dnd_bind("<<Drop>>", lambda e: _img_add(_split_dnd_paths(e.data)))

        # ====== (3) テキスト入力領域（最小高さ=DROPと同じ、そこから拡大自由） ======
        text_container = ttk.Frame(center)
        text_frame = ttk.Frame(text_container)
        text_frame.pack(fill="both", expand=True)
        send_box = tk.Text(text_frame, height=DROP_H_LINES, wrap="word")
        send_box.pack(fill="both", expand=True)
        # 3 段目（テキスト入力）。最小高さ＝DROPと同じ。拡大はユーザー操作で自由
        center.add(text_container, weight=0)

        # ===== 高さ制御: minsize 非対応環境のため sashpos で固定/最小高さを再現 =====
        # 行のピクセル高を取得（Tkデフォルトフォントの行間を利用）
        try:
            import tkinter.font as tkfont
            line_px = tkfont.Font(root=w, name='TkDefaultFont', exists=True).metrics('linespace')
        except Exception:
            line_px = 18  # フォールバック
        DROP_H_PX = DROP_H_LINES * line_px
        TEXT_MIN_PX = DROP_H_PX

        def _enforce_layout(event=None):
            """Panedwindow のサッシ位置を調整して、
               上：可変 / 中：固定高(DROP_H_PX) / 下：最小高(TEXT_MIN_PX) を守る"""
            center.update_idletasks()
            H = center.winfo_height()
            # 上段(チャット)の高さは H - (中固定 + 下最小) を下限80で確保
            chat_h = max(80, H - (DROP_H_PX + TEXT_MIN_PX))
            s0 = chat_h                    # 1本目のサッシ位置（上端からのpx）
            s1 = chat_h + DROP_H_PX        # 2本目のサッシ位置
            try:
                center.sashpos(0, s0)
                center.sashpos(1, s1)
            except Exception:
                pass

        # 初期配置とリサイズ時に反映
        center.bind("<Configure>", _enforce_layout)
        w.after(0, _enforce_layout)

        # ====== 下部固定ツールバー（常時表示） ======
        footer = ttk.Frame(w)
        footer.pack(side="bottom", fill="x", padx=8, pady=(0,8))
        ttk.Label(footer, text="Target").pack(side="left")
        var_img_lang = tk.StringVar(value=var_lang.get() or "en")
        ttk.Combobox(
            footer, textvariable=var_img_lang, width=8,
            values=["en","ja","zh","ko","es","fr","de","it","pt","ru","id","vi","th"]
        ).pack(side="left", padx=6)
        # ご要望：Pick の左に Send を配置。ボタンは左→右で: Send, Pick, Translate, Pause, Resume, Stop
        btn_send = ttk.Button(footer, text="Send", command=lambda: _send())
        btn_pick = ttk.Button(footer, text="Pick image(s)…", command=_pick_files)
        btn_tr   = ttk.Button(footer, text="Translate")
        btn_ps   = ttk.Button(footer, text="Pause")
        btn_rs   = ttk.Button(footer, text="Resume")
        btn_st   = ttk.Button(footer, text="Stop")
        # 左から順に並べ、その後に右寄せスペーサーを入れて押し流しを防ぐ
        btn_send.pack(side="left", padx=(0,6))
        btn_pick.pack(side="left", padx=(0,12))
        btn_tr.pack(side="left", padx=(0,6))
        btn_ps.pack(side="left", padx=(0,6))
        btn_rs.pack(side="left", padx=(0,6))
        btn_st.pack(side="left", padx=(0,0))

        # worker
        stop_flag = {"v": False}
        def _run_translate():
            stop_flag["v"] = False
            lang = (var_img_lang.get() or "en").strip()
            for p in list(pending_images):
                if stop_flag["v"]: break
                while paused["v"] and not stop_flag["v"]:
                    time.sleep(0.1)
                try:
                    # Windows→Pi 間でパスは通らないので、中身をBase64で送る
                    with open(p, "rb") as f:
                        import base64
                        b64 = base64.b64encode(f.read()).decode("ascii")
                    payload = {
                        "console": name,
                        "filename": Path(p).name,
                        "b64": b64,
                        "lang": lang,
                    }
                    http_post("/send_image", payload, timeout=300)
                    tshow = datetime.now().strftime("%H:%M:%S")
                    self._append_log(f"[{tshow}] you → [{name}] (img→{lang}) {Path(p).name}")
                except Exception as ex:
                    messagebox.showerror("Image translate failed", str(ex))
            pending_images.clear(); _refresh_drop()

        def _start_tr():
            threading.Thread(target=_run_translate, daemon=True).start()
        def _pause(): paused["v"] = True
        def _resume(): paused["v"] = False
        def _stop(): stop_flag["v"] = True; paused["v"] = False
        btn_tr.configure(command=_start_tr)
        btn_ps.configure(command=_pause)
        btn_rs.configure(command=_resume)
        btn_st.configure(command=_stop)

        # ===== 送信処理（Enter=送信 / Ctrl+Enter=改行） =====
        def _send(_=None):
            t = send_box.get("1.0","end").strip()
            if not t: return
            try:
                payload = {"console": name, "text": t}
                lng = (var_lang.get() or "").strip()
                if lng and lng.lower() != "auto":
                    payload["lang"] = lng
                http_post("/send", payload, timeout=30)
                send_box.delete("1.0","end")
                ts = datetime.now().strftime("%H:%M:%S")
                shown_lang = payload.get("lang", route.get("lang",""))
                txt.insert(tk.END, f"[{ts}] you → [{name}] ({shown_lang}) {t}\n"); txt.see(tk.END)

            except Exception as ex:
                messagebox.showerror("Send failed", str(ex))
        def _on_return(ev):
            # Shift/Ctrl+Enter = 改行, 単独Enter = 送信
            if ev.state & 0x4:   # Ctrl
                return
            if ev.state & 0x1:   # Shift
                return
            _send(); return "break"
        send_box.bind("<Return>", _on_return)

        self._chat_windows = getattr(self, "_chat_windows", [])
        self._chat_windows.append((name, route, txt))
        # クローズ時にリストから掃除
        def _on_close():
            try:
                self._chat_windows = [(n, r, t) for (n, r, t) in self._chat_windows if t is not txt]
                self.history_offset.pop(name, None)
            except Exception:
                pass
            w.destroy()
        w.protocol("WM_DELETE_WINDOW", _on_close)

    # ---- 追加：Monitor ----
    def _poll_stats(self):
        try:
            r = requests.get(API_BASE + "/stats", timeout=2)
            data = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
            if r.ok and data.get("ok"):
                s = data["stats"]
                lines = [
                    f"ready: {s.get('ready')}",
                    f"session: {s.get('session_id')}",
                    f"api: http://{s.get('api_host')}:{s.get('api_port')}",
                    f"bindings: {s.get('bindings')}",
                    f"queue: {s.get('queue')}",
                    f"last_error: {s.get('last_error')}",
                    "routes:",
                ]
                for k,v in (s.get("routes") or {}).items():
                    lines.append(f"  - {k}: {v}")
                self.txt_mon.delete("1.0","end")
                self.txt_mon.insert("end","\n".join(lines))
            else:
                self.txt_mon.delete("1.0","end"); self.txt_mon.insert("end", f"(stats) HTTP {r.status_code}")
        except Exception as e:
            self.txt_mon.delete("1.0","end"); self.txt_mon.insert("end", f"(stats error) {e}")
        finally:
            self.after(1000, self._poll_stats)

    def _append_log(self, line: str):
        self.txt_log.insert(tk.END, line + "\n")
        self.txt_log.see(tk.END)
    # ===================== File Transfer methods =====================
    def _ft_log(self, s: str):
        self.ft_log.insert("end", s + "\n"); self.ft_log.see("end"); self.update_idletasks()

    def _ft_clear_preview(self):
        self.ft_preview.delete("1.0","end"); self.ft_preview.update_idletasks()

    def _ft_append_preview(self, s: str):
        self.ft_preview.insert("end", s); self.ft_preview.see("end"); self.ft_preview.update_idletasks()

    def _ft_on_drop(self, event):
        paths = self._ft_split_paths(event.data)
        self._ft_start_worker(paths)

    def _ft_pick_files(self):
        paths = filedialog.askopenfilenames(filetypes=[
            ("Text-like","*.txt *.md *.rst *.html *.htm *.srt"),
            ("All files","*.*"),
        ])
        if paths: self._ft_start_worker(list(paths))

    def _ft_start_worker(self, paths: list[str]):
        # ▼ 毎回フラグを初期化（前回の Pause/Stop をリセット）
        try:
            self.ft_pause.clear()
            self.ft_stop.clear()
            # UI のボタンもリセット
            if hasattr(self, "btn_ft_pause"):
                self.btn_ft_pause.config(text="Pause")
        except Exception:
            pass
        t = threading.Thread(target=self._ft_process_files, args=(paths,), daemon=True)
        t.start()

    def _ft_process_files(self, paths: list[str]):
        # OpenAIキーが .env 保存後に変わった可能性があるので都度見る
        if not os.getenv("OPENAI_API_KEY") and not OPENAI_API_KEY:
            self._ft_log("ERROR: OPENAI_API_KEY is not set."); return
        # 既存クライアントが無ければ作る
        if not self.ft_client:
            key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY)
            self.ft_client = OpenAI(api_key=key)

        target_lang = (self.ft_var_lang.get() or DEFAULT_TARGET).strip()
        plan = _ChunkPlan(max_tokens=max(800, int(self.ft_var_max.get() or 3500)))
        for raw in paths:
            p = Path(raw.strip().strip("{}"))
            if not p.exists(): self._ft_log(f"Skip: not found -> {p}"); continue
            if not _ft_is_supported(p): self._ft_log(f"Skip: unsupported -> {p.name}"); continue
            try:
                self._ft_log(f"Reading: {p}")
                text = p.read_text(encoding=_ft_infer_encoding(p))
            except Exception as e:
                self._ft_log(f"ERROR reading {p.name}: {e}"); continue

            self._ft_clear_preview()
            self._ft_append_preview(f"# Translating: {p.name}\n\n")
            self._ft_log("Chunking…")
            chunks = _chunk_text(text, plan)
            self._ft_log(f"{len(chunks)} chunk(s). Translating to {target_lang}…")
            try:
                translated = _translate_long_text_stream(
                    self.ft_client, text, target_lang, plan,
                    on_progress=self._ft_log,
                    on_preview=self._ft_append_preview,
                    should_pause=(lambda: self.ft_pause.is_set()),
                    should_stop =(lambda: self.ft_stop.is_set())
                )
            except Exception as e:
                # ユーザー中止は静かにログして次ファイルへ
                if "translation-stopped" in str(e):
                    self._ft_log("Stopped by user.")
                    continue
                # それ以外は既存エラー処理
                self._ft_log(f"ERROR translating {p.name}: {e}"); continue

            out = _ft_out_path(p, target_lang)
            try:
                out.write_text(translated, encoding="utf-8")
                self._ft_log(f"Saved: {out} ({len(translated)} chars)")
            except Exception as e:
                self._ft_log(f"ERROR writing {out.name}: {e}")

    @staticmethod
    def _ft_split_paths(dnd: str) -> list[str]:
        items, buf, in_brace = [], "", False
        for ch in dnd:
            if ch == "{": in_brace = True; buf = ""
            elif ch == "}": in_brace = False; items.append(buf)
            elif ch == " " and not in_brace:
                if buf: items.append(buf); buf = ""
            else: buf += ch
        if buf: items.append(buf)
        return items

    def destroy(self):
        try:
            if self.tailer: self.tailer.stop()
        except Exception:
            pass
        super().destroy()

if __name__ == "__main__":
    App().mainloop()
