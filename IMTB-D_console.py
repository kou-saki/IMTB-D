# -*- coding: utf-8 -*-
import argparse, json, sys, time
from pathlib import Path
import requests

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parent
LOG_DIR    = SCRIPT_DIR / "log"
JSONL_PATH = LOG_DIR / "messages.jsonl"
API_BASE = "http://127.0.0.1:8765"

def api_post(path, payload):
    r = requests.post(API_BASE + path, json=payload, timeout=30)
    # サーバのJSONを読んで、ok:falseならそのerrorを投げる
    try:
        data = r.json()
    except Exception:
        r.raise_for_status()
        return {}
    if not r.ok or not data.get("ok", False):
        # /send側で作った "error" を優先表示
        raise RuntimeError(data.get("error", f"HTTP {r.status_code}"))
    return data

def tail_jsonl(filters: dict):
    print(f"[tail] {JSONL_PATH} filters={filters}")
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSONL_PATH.touch(exist_ok=True)
    with JSONL_PATH.open("r", encoding="utf-8") as f:
        f.seek(0, 2)
        buf = ""
        while True:
            chunk = f.read()
            if not chunk:
                time.sleep(0.3); continue
            buf += chunk
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if not line.strip(): continue
                try: rec = json.loads(line)
                except Exception: continue
                if match(rec, filters): render(rec)

def match(rec, filters):
    if filters.get("type") == "dm":
        pid = int(filters["user_id"])
        if rec.get("direction","").startswith("dm_") or rec.get("direction","").endswith("_dm"):
            if rec.get("user_id")==pid or rec.get("to_user_id")==pid: return True
    elif filters.get("type") == "channel":
        if rec.get("channel_id") == int(filters["channel_id"]): return True
    return False

def render(rec):
    prefix = "you →" if rec.get("direction") in ("outbound","outbound_dm") else "them →"
    to_lang = rec.get("to_lang")
    ch = rec.get("channel_name") or rec.get("channel_id") or rec.get("user_name") or rec.get("user_id")
    txt = rec.get("translated") or rec.get("original")
    print(f"{prefix} [{ch}] ({to_lang}) {txt}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dm", type=int)
    g.add_argument("--channel", type=int)
    ap.add_argument("--lang", default="")
    args = ap.parse_args()

    payload = {"console": args.name, "type": "dm", "user_id": args.dm, "lang": args.lang} if args.dm \
              else {"console": args.name, "type": "channel", "channel_id": args.channel, "lang": args.lang}
    try:
        resp = api_post("/bind", payload)
        if not resp.get("ok"): print("[bind] failed:", resp); sys.exit(1)
        print(f"[bind] ok: {payload}")
    except Exception as e:
        print(f"[bind] error: {e}")
        print("※ 先に babel_relay.py を起動しておいてください。"); sys.exit(1)

    import threading
    def input_loop():
        for line in sys.stdin:
            text = line.rstrip("\n")
            if not text: continue
            try:
                r = api_post("/send", {"console": args.name, "text": text})
                if not r.get("ok"): print("[send] failed:", r)
            except Exception as e:
                print(f"[send] error: {e}")
    threading.Thread(target=input_loop, daemon=True).start()

    filt = {"type":"dm","user_id":args.dm} if args.dm else {"type":"channel","channel_id":args.channel}
    tail_jsonl(filt)

if __name__ == "__main__":
    main()
