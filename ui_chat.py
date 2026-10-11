# -*- coding: utf-8 -*-
# Message Session window. Python 3.4 compatible.
# History opens a disk-log window (server-side), not a local clear.

import tkinter as tk

import icons
import sound


BG = "#c0c0c0"

CH_META = {
    "ALL": ("ALL", u"\u041e\u0431\u0449\u0438\u0439 \u0447\u0430\u0442"),
    "A":   ("8766", u"\u0410\u0440\u043a\u0430\u0434\u0438\u0439"),
    "B":   ("8767", u"\u0411\u043e\u0440\u0438\u0441"),
    "C":   ("8768", u"\u0421\u0435\u043c\u0451\u043d"),
    "D":   ("8769", u"\u0414\u0438\u043c\u043e\u043d"),
}

BASH_CODE = ":bash:"


class BashAnimation(object):
    FRAMES = [(0, 0, False), (-3, 0, True), (0, 0, False), (3, 0, True)]

    def __init__(self, master):
        self.win = tk.Toplevel(master)
        self.win.title(u"\u0411\u0430\u0448")
        self.win.configure(bg="#ffffcc")
        self.win.geometry("140x140")
        self.win.resizable(False, False)
        self.win.transient(master)

        self.canvas = tk.Canvas(self.win, width=140, height=120,
                                bg="#ffffcc", bd=0, highlightthickness=0)
        self.canvas.pack()

        self.idx = 0
        self.alive = True
        self._tick()

    def _draw(self, dx, dy, star):
        c = self.canvas
        c.delete("all")
        c.create_rectangle(20, 10, 26, 110, fill="#884400", outline="#442200", width=2)
        c.create_line(23, 20, 23, 100, fill="#664400", dash=(2, 2))
        cx = 70 + dx
        cy = 60 + dy
        c.create_oval(cx - 25, cy - 25, cx + 25, cy + 25,
                      fill="#ffd700", outline="#000000", width=2)
        c.create_line(cx - 14, cy - 6, cx - 6, cy - 6, fill="#000000", width=2)
        c.create_line(cx + 6, cy - 6, cx + 14, cy - 6, fill="#000000", width=2)
        c.create_arc(cx - 10, cy + 2, cx + 10, cy + 18,
                     start=180, extent=180, style="arc",
                     outline="#000000", width=2)
        c.create_oval(cx - 30, cy - 6, cx - 20, cy + 6,
                      fill="#ffd700", outline="#000000", width=2)
        if star:
            sx, sy = 32, 30
            c.create_polygon(sx, sy - 8, sx + 3, sy - 2, sx + 9, sy - 2,
                             sx + 4, sy + 2, sx + 6, sy + 8,
                             sx, sy + 4, sx - 6, sy + 8, sx - 4, sy + 2,
                             sx - 9, sy - 2, sx - 3, sy - 2,
                             fill="#ff3300", outline="#660000")

    def _tick(self):
        if not self.alive:
            return
        f = self.FRAMES[self.idx % len(self.FRAMES)]
        self._draw(f[0], f[1], f[2])
        self.idx += 1
        self.win.after(180, self._tick)

    def close(self):
        self.alive = False
        try:
            self.win.destroy()
        except Exception:
            pass


class HistoryWindow(object):
    """Read-only viewer of server-side log for the channel."""

    def __init__(self, master, api, ch, title):
        self.api = api
        self.ch = ch

        self.win = tk.Toplevel(master)
        self.win.title(title)
        self.win.geometry("640x480")
        self.win.configure(bg=BG)

        top = tk.Frame(self.win, bg=BG)
        top.pack(fill="x", padx=4, pady=4)

        tk.Button(top, text="Reload", font=("MS Sans Serif", 8),
                  command=self.reload, bd=1, relief="raised", bg=BG).pack(side="left")
        tk.Button(top, text="Close", font=("MS Sans Serif", 8),
                  command=self.win.destroy, bd=1, relief="raised", bg=BG).pack(side="right")
        self.lbl = tk.Label(top, text="", bg=BG, font=("MS Sans Serif", 8))
        self.lbl.pack(side="left", padx=8)

        wrap = tk.Frame(self.win, bg=BG)
        wrap.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.text = tk.Text(wrap, wrap="word",
                            font=("Courier New", 9),
                            bg="white", bd=2, relief="sunken")
        sb = tk.Scrollbar(wrap, command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self.reload()

    def reload(self):
        self.lbl.configure(text="loading...")
        if self.ch == "ALL":
            r = self.api.logs("chat")
            raw = ""
            if r.get("ok"):
                raw = r["data"].get("content") or ""
            self.text.delete("1.0", "end")
            self.text.insert("end", raw)
            self.lbl.configure(text="chat.jsonl, " + str(len(raw)) + " bytes")
        else:
            r = self.api.chat(self.ch)
            self.text.delete("1.0", "end")
            if r.get("ok"):
                msgs = r["data"].get("messages") or []
                for m in msgs:
                    self.text.insert("end", "[" + m.get("time", "") + "] "
                                     + str(m.get("from", "?")) + "\n")
                    self.text.insert("end", "  " + str(m.get("text", "")) + "\n\n")
                self.lbl.configure(text="personal " + self.ch + ", " + str(len(msgs)) + " msgs")
            else:
                self.lbl.configure(text="error")


class ChatWindow(object):
    def __init__(self, root, api, state, ch, label, nick="operator", on_close=None):
        self.api = api
        self.state = state
        self.ch = ch
        self.label = label
        self.nick = nick
        self.on_close = on_close
        self.bash_win = None

        meta = CH_META.get(ch) or ("?", ch)
        self.agent_name = meta[1]
        self.agent_port = meta[0]

        self.win = tk.Toplevel(root)
        self.win.configure(bg=BG)
        self.win.geometry("560x480")
        self.win.minsize(480, 380)

        self.icons = icons.IconSet(self.win)
        self._build()

        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.win.after(200, self._first_pull)
        self._schedule_poll()

    def _build(self):
        self.win.title(self.agent_name + " - Message Session")

        top = tk.Frame(self.win, bg=BG)
        top.pack(side="top", fill="x", padx=4, pady=4)

        tk.Label(top, text="To:", bg=BG, font=("MS Sans Serif", 8)).grid(row=0, column=0, sticky="w")
        tk.Label(top, text=self.agent_port, bg=BG, font=("MS Sans Serif", 8, "bold"),
                 fg="#000080").grid(row=0, column=1, sticky="w", padx=(4, 12))
        tk.Label(top, text="Nick:", bg=BG, font=("MS Sans Serif", 8)).grid(row=0, column=2, sticky="w")
        tk.Label(top, text=self.agent_name, bg=BG, font=("MS Sans Serif", 8, "bold"),
                 fg="#000080").grid(row=0, column=3, sticky="w", padx=(4, 12))
        tk.Label(top, text="From:", bg=BG, font=("MS Sans Serif", 8)).grid(row=0, column=4, sticky="w")
        tk.Label(top, text=self.nick, bg=BG, font=("MS Sans Serif", 8)).grid(row=0, column=5, sticky="w", padx=(4, 0))

        btns = tk.Frame(self.win, bg=BG)
        btns.pack(side="bottom", fill="x", padx=4, pady=(2, 6))
        tk.Button(btns, text="Cancel", font=("MS Sans Serif", 8), width=8,
                  command=self.close, bd=1, relief="raised", bg=BG).pack(side="right", padx=(4, 0))
        tk.Button(btns, text="Send", font=("MS Sans Serif", 8), width=8,
                  command=self._send, bd=1, relief="raised", bg=BG).pack(side="right")
        tk.Button(btns, text="Bash", font=("MS Sans Serif", 8), width=6,
                  command=self._bash, bd=1, relief="raised", bg="#ffd700").pack(side="left")
        tk.Button(btns, text="History", font=("MS Sans Serif", 8), width=8,
                  command=self._history, bd=1, relief="raised", bg=BG).pack(side="left", padx=(4, 0))

        info = tk.Frame(self.win, bg=BG)
        info.pack(side="bottom", fill="x", padx=4)
        self.lbl_chars = tk.Label(info, text="Chars: 0", bg=BG, font=("MS Sans Serif", 8))
        self.lbl_chars.pack(side="left")

        inp = tk.Frame(self.win, bg=BG)
        inp.pack(side="bottom", fill="x", padx=4, pady=(2, 2))
        self.entry = tk.Text(inp, height=4, wrap="word",
                             font=("Courier New", 9),
                             bg="white", bd=2, relief="sunken")
        self.entry.pack(fill="both", expand=True)
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<KeyRelease>", lambda e: sound.typekey(), add="+")
        self.entry.bind("<Control-Return>", self._send)

        hist_wrap = tk.Frame(self.win, bg=BG)
        hist_wrap.pack(side="top", fill="both", expand=True, padx=4, pady=(0, 2))
        self.hist = tk.Text(hist_wrap, wrap="word",
                            font=("Courier New", 9),
                            bg="white", bd=2, relief="sunken")
        sb = tk.Scrollbar(hist_wrap, command=self.hist.yview)
        self.hist.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.hist.pack(side="left", fill="both", expand=True)
        self.hist.configure(state="disabled")

    def _on_key(self, evt=None):
        try:
            n = len(self.entry.get("1.0", "end-1c"))
        except Exception:
            n = 0
        self.lbl_chars.configure(text="Chars: " + str(n))

    def _bash(self):
        try:
            if self.bash_win:
                self.bash_win.close()
        except Exception:
            pass
        self.bash_win = BashAnimation(self.win)
        try:
            self.entry.insert("insert", " " + BASH_CODE + " ")
            self._on_key()
        except Exception:
            pass

    def _history(self):
        HistoryWindow(self.win, self.api, self.ch,
                      self.agent_name + " - History")

    def _send(self, evt=None):
        text = self.entry.get("1.0", "end-1c").strip()
        if not text:
            return "break"
        self.entry.delete("1.0", "end")
        self.lbl_chars.configure(text="Chars: 0")
        if self.ch == "ALL":
            r = self.api.send_all(text)
        else:
            r = self.api.send_personal(self.ch, text)
        if r.get("ok"):
            try:
                sound.sent()
            except Exception:
                pass
            self._append("SYS", "sent")
        else:
            self._append("ERR", str(r.get("error"))[:120])
        self.win.after(400, self._pull)
        return "break"

    def _first_pull(self):
        self._pull(full=True)

    def _pull(self, full=False):
        if self.ch == "ALL":
            r = self.api.messages_all()
        else:
            r = self.api.chat(self.ch)
        if not r.get("ok"):
            return
        if self.ch == "ALL":
            data = r["data"]
            msgs = data if isinstance(data, list) else (data.get("messages") or [])
        else:
            msgs = r["data"].get("messages") or []
        self._render(msgs)
        self.state.mark_seen(self.ch, msgs=msgs)

    def _render(self, msgs):
        self.hist.configure(state="normal")
        self.hist.delete("1.0", "end")
        for m in msgs[-200:]:
            frm = m.get("from", "?")
            txt = m.get("text", "")
            tm = m.get("time", "")
            self.hist.insert("end", "[" + tm + "] " + frm + "\n")
            if BASH_CODE in txt:
                txt = txt.replace(BASH_CODE, u"[\u0411\u0410\u0428!]")
            self.hist.insert("end", "  " + txt + "\n\n")
        self.hist.see("end")
        self.hist.configure(state="disabled")

    def _append(self, who, text):
        self.hist.configure(state="normal")
        self.hist.insert("end", "[" + who + "] " + text + "\n")
        self.hist.see("end")
        self.hist.configure(state="disabled")

    def _schedule_poll(self):
        self.win.after(4000, self._poll_tick)

    def _poll_tick(self):
        try:
            self._pull(full=False)
        except Exception:
            pass
        self._schedule_poll()

    def close(self):
        try:
            if self.bash_win:
                self.bash_win.close()
        except Exception:
            pass
        try:
            if self.on_close:
                self.on_close(self.ch)
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass