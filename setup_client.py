# -*- coding: utf-8 -*-
# Installer / first-run wizard for JewAIXP client (XP / Python 3.4).
# Configures xp_client.json, runs a ping test.

import os
import io
import json
import sys
import socket

try:
    import urllib.request as _url
except ImportError:
    import urllib2 as _url


HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "xp_client.example.json")
CONFIG = os.path.join(HERE, "xp_client.json")


def w(s):
    try:
        print(s)
    except Exception:
        print(str(s).encode("ascii", "replace").decode("ascii"))


def load_example():
    cfg = {
        "server": "http://192.168.1.24:8770",
        "nick": "operator",
        "poll_ms": 4000,
        "font_size": 9,
    }
    if os.path.isfile(EXAMPLE):
        try:
            f = io.open(EXAMPLE, "r", encoding="utf-8")
            try:
                d = json.load(f)
                for k in d:
                    cfg[k] = d[k]
            finally:
                f.close()
        except Exception:
            pass
    return cfg


def save(cfg):
    f = io.open(CONFIG, "w", encoding="utf-8")
    try:
        f.write(json.dumps(cfg, ensure_ascii=False, indent=2))
    finally:
        f.close()


def ping(server):
    url = server.rstrip("/") + "/api/state"
    try:
        r = _url.urlopen(url, timeout=5)
        body = r.read().decode("utf-8", "replace")
        return True, body[:200]
    except Exception as e:
        return False, repr(e)[:200]


def main():
    w("=== JewAIXP client setup ===")
    w("")
    w("This wizard creates xp_client.json and tests connection.")
    w("")

    cfg = load_example()

    srv = input("Mainframe URL [%s]: " % cfg["server"]).strip()
    if srv:
        cfg["server"] = srv
    nick = input("Your nick [%s]: " % cfg["nick"]).strip()
    if nick:
        cfg["nick"] = nick

    save(cfg)
    w("")
    w("saved to: " + CONFIG)
    w("")

    w("testing connection to " + cfg["server"] + " ...")
    ok, detail = ping(cfg["server"])
    if ok:
        w("[ OK ] mainframe responds")
        w("       " + detail)
    else:
        w("[FAIL] no response: " + detail)
        w("check firewall, mainframe running, IP correct")

    w("")
    w("Now run run_client.bat to start.")
    w("")
    input("Press Enter to close...")


if __name__ == "__main__":
    main()