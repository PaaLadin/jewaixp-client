# -*- coding: utf-8 -*-
# HTTP client for council_chat mainframe. Python 3.4 compatible.

import json

try:
    import urllib.request as _url
except ImportError:
    import urllib2 as _url


class Api(object):
    def __init__(self, base, nick="operator", timeout=8):
        self.base = (base or "").rstrip("/")
        self.nick = nick
        self.timeout = timeout

    def set_base(self, base):
        self.base = (base or "").rstrip("/")

    def set_nick(self, nick):
        self.nick = nick

    def _get(self, path):
        try:
            r = _url.urlopen(self.base + path, timeout=self.timeout)
            body = r.read().decode("utf-8", "replace")
            return {"ok": True, "data": json.loads(body)}
        except Exception as e:
            return {"ok": False, "error": repr(e)[:200]}

    def _post(self, path, payload):
        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        except Exception as e:
            return {"ok": False, "error": "json: " + repr(e)[:100]}
        req = _url.Request(self.base + path, data=data)
        req.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            r = _url.urlopen(req, timeout=self.timeout)
            body = r.read().decode("utf-8", "replace")
            return {"ok": True, "data": json.loads(body)}
        except Exception as e:
            return {"ok": False, "error": repr(e)[:200]}

    # --- endpoints ---

    def state(self):
        return self._get("/api/state")

    def status(self):
        return self._get("/api/status")

    def meeting(self):
        return self._get("/api/meeting")

    def messages_all(self):
        return self._get("/api/messages")

    def chat(self, ch):
        return self._get("/api/chat/" + ch)

    def logs(self, name="chat"):
        return self._get("/api/logs?name=" + name)

    def send_all(self, text):
        return self._post("/api/send", {"from": self.nick, "to": "ALL", "text": text})

    def send_personal(self, ch, text):
        return self._post("/api/chat/" + ch, {"from": self.nick, "text": text})

    def pause_all(self, on):
        return self._post("/api/pause_all", {"on": bool(on)})

    def meeting_on(self, on):
        return self._post("/api/meeting", {"on": bool(on)})