# -*- coding: utf-8 -*-
# Local unread tracker. Python 3.4 compatible.
# mark_seen uses max(ts of msgs) so channel clocks may differ safely.

import os
import io
import json
import time


STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unread.json")


class State(object):
    def __init__(self, path=None):
        self.path = path or STATE_FILE
        self.seen_ts = {}
        self.unread_count = {}
        self._load()

    def _load(self):
        if not os.path.isfile(self.path):
            return
        try:
            f = io.open(self.path, "r", encoding="utf-8")
            try:
                d = json.load(f)
            finally:
                f.close()
            self.seen_ts = d.get("seen_ts", {}) or {}
            self.unread_count = d.get("unread_count", {}) or {}
            for k in list(self.seen_ts.keys()):
                try:
                    self.seen_ts[k] = float(self.seen_ts[k])
                except Exception:
                    self.seen_ts[k] = 0.0
            for k in list(self.unread_count.keys()):
                try:
                    self.unread_count[k] = int(self.unread_count[k])
                except Exception:
                    self.unread_count[k] = 0
        except Exception:
            pass

    def save(self):
        try:
            f = io.open(self.path, "w", encoding="utf-8")
            try:
                f.write(json.dumps({
                    "seen_ts": self.seen_ts,
                    "unread_count": self.unread_count,
                    "saved": time.time()
                }, ensure_ascii=False, indent=2))
            finally:
                f.close()
        except Exception:
            pass

    def last_seen(self, ch):
        return float(self.seen_ts.get(ch, 0.0))

    def max_ts(self, msgs):
        m = 0.0
        for x in msgs:
            try:
                t = float(x.get("ts") or 0)
            except Exception:
                t = 0.0
            if t > m:
                m = t
        return m

    def mark_seen(self, ch, ts=None, msgs=None):
        """Mark channel as read. If msgs passed, use their max ts as cutoff.
        This avoids clock skew between XP and server."""
        if msgs:
            ts = self.max_ts(msgs)
            if ts <= 0:
                ts = self.last_seen(ch) or time.time()
        if ts is None:
            ts = time.time()
        self.seen_ts[ch] = float(ts)
        self.unread_count[ch] = 0
        self.save()

    def count_new(self, ch, msgs):
        cutoff = self.last_seen(ch)
        n = 0
        for m in msgs:
            try:
                ts = float(m.get("ts") or 0)
            except Exception:
                ts = 0.0
            if ts > cutoff:
                n += 1
        return n

    def update_unread(self, ch, msgs, opened=False):
        if opened:
            self.mark_seen(ch, msgs=msgs)
            return 0
        n = self.count_new(ch, msgs)
        self.unread_count[ch] = n
        self.save()
        return n

    def unread(self, ch):
        return int(self.unread_count.get(ch, 0))

    def total_unread(self):
        total = 0
        for k in self.unread_count:
            total += int(self.unread_count[k] or 0)
        return total

    def reset_all(self):
        self.seen_ts = {}
        self.unread_count = {}
        self.save()