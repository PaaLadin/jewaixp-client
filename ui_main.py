# -*- coding: utf-8 -*-
# Main ICQ window. Contact list uses small (8x8) icons.
# Names are bold when channel unread and agent online.

import tkinter as tk
from tkinter import messagebox, font as tkfont

import icons
import state as st_mod
import sound


BG = "#c0c0c0"
SEL_BG = "#000080"
SEL_FG = "#ffffff"

FONT_NORM_TUPLE = ("MS Sans Serif", 8)
FONT_NORM = FONT_NORM_TUPLE
FONT_BOLD = None   # set after root exists

# channel -> display name
CH_NAMES = {
    "ALL": u"\u041e\u0431\u0449\u0438\u0439",
    "A":   u"\u0410\u0440\u043a\u0430\u0434\u0438\u0439",
    "B":   u"\u0411\u043e\u0440\u0438\u0441",
    "C":   u"\u0421\u0435\u043c\u0451\u043d",
    "D":   u"\u0414\u0438\u043c\u043e\u043d",
}


class MainWindow(object):
    def __init__(self, root, api, cfg, on_open_chat, on_settings, on_pause_all):
        self.root = root
        self.api = api
        self.cfg = cfg
        self.on_open_chat = on_open_chat
        self.on_settings = on_settings
        self.on_pause_all = on_pause_all

        self.state = st_mod.State()
        self.icons = icons.IconSet(root)
        self.channels = ["ALL"]
        self.blink_on = False
        self.rows = {}  # ch -> {"image":name, "name_id":..., "base":kind, "tag":tag, "open":bool, "bold":bool}

        self._init_fonts()
        self._build()
        self.refresh_channels()
        self._schedule_blink()
        self._schedule_poll()

    def _init_fonts(self):
        global FONT_BOLD
        try:
            FONT_BOLD = ("MS Sans Serif", 8, "bold")
        except Exception:
            FONT_BOLD = None

    def _build(self):
        self.root.title("JewAIXP")
        self.root.geometry("260x420")
        self.root.minsize(240, 340)
        self.root.configure(bg=BG)

        m = tk.Menu(self.root)
        filem = tk.Menu(m, tearoff=0)
        filem.add_command(label="Settings...", command=self.on_settings)
        filem.add_separator()
        self._sound_on = True
        filem.add_command(label="Sound on/off", command=self._toggle_sound)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.root.destroy)
        m.add_cascade(label="File", menu=filem)

        servm = tk.Menu(m, tearoff=0)
        servm.add_command(label="Refresh", command=self.refresh_channels)
        servm.add_command(label="PAUSE-ALL", command=self.on_pause_all)
        m.add_cascade(label="Service", menu=servm)

        helpm = tk.Menu(m, tearoff=0)
        helpm.add_command(label="About", command=self._about)
        m.add_cascade(label="Help", menu=helpm)
        self.root.config(menu=m)

        tb = tk.Frame(self.root, bg=BG, bd=1, relief="raised")
        tb.pack(fill="x")
        self.ico_logo = self.icons.get("online", "normal")
        tk.Label(tb, image=self.ico_logo, bg=BG).pack(side="left", padx=2, pady=2)
        tk.Button(tb, text="Add", width=4, font=FONT_NORM,
                  command=self._noop, bd=1, relief="raised", bg=BG).pack(side="left", padx=1)
        tk.Button(tb, text="Srv", width=4, font=FONT_NORM,
                  command=self.on_settings, bd=1, relief="raised", bg=BG).pack(side="left", padx=1)
        tk.Button(tb, text="ICQ", width=4, font=FONT_NORM,
                  command=self.refresh_channels, bd=1, relief="raised", bg=BG).pack(side="left", padx=1)

        wrap = tk.Frame(self.root, bg=BG)
        wrap.pack(fill="both", expand=True, padx=2, pady=2)

        self.contacts = tk.Text(wrap, font=FONT_NORM,
                                bd=2, relief="sunken", bg=BG,
                                cursor="arrow", wrap="none",
                                height=16, state="disabled")
        sb = tk.Scrollbar(wrap, command=self.contacts.yview)
        self.contacts.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.contacts.pack(side="left", fill="both", expand=True)
        self.contacts.bind("<Key>", lambda e: "break")
        try:
            self.contacts.tag_configure("bold", font=("MS Sans Serif", 8, "bold"))
        except Exception:
            self.contacts.tag_configure("bold", font=FONT_NORM)
        self.contacts.tag_configure("norm", font=FONT_NORM)
        self.contacts.bind("<Double-Button-1>", self._on_text_dbl)
        self.contacts.bind("<Button-1>", self._on_text_click)

        sf = tk.Frame(self.root, bg=BG)
        sf.pack(fill="x", padx=2)
        tk.Label(sf, text="Find:", bg=BG, font=FONT_NORM).pack(side="left")
        self.search = tk.Entry(sf, font=FONT_NORM, bd=2, relief="sunken")
        self.search.pack(side="left", fill="x", expand=True, padx=2)
        self.search.bind("<KeyRelease>", lambda e: self._rebuild_list())

        bf = tk.Frame(self.root, bg=BG)
        bf.pack(fill="x", padx=2, pady=2)
        tk.Button(bf, text="COUNCIL", font=FONT_NORM, width=7,
                  command=self.on_council, bd=1, relief="raised", bg="#ffe080").pack(side="left", padx=1)
        tk.Button(bf, text="PAUSE", font=FONT_NORM, width=6,
                  command=self.on_pause_all, bd=1, relief="raised", bg="#ffb080").pack(side="left", padx=1)
        tk.Button(bf, text="RESUME", font=FONT_NORM, width=6,
                  command=self.on_resume, bd=1, relief="raised", bg="#a0ffa0").pack(side="left", padx=1)
        tk.Button(bf, text="Logs", font=FONT_NORM, width=5,
                  command=self.on_logs, bd=1, relief="raised", bg=BG).pack(side="right", padx=1)

        sb2 = tk.Frame(self.root, bg=BG, bd=1, relief="sunken")
        sb2.pack(fill="x", side="bottom")
        self.ico_stat = self.icons.get("offline", "normal")
        self.lbl_stat_icon = tk.Label(sb2, image=self.ico_stat, bg=BG)
        self.lbl_stat_icon.pack(side="left", padx=2)
        self.lbl_stat = tk.Label(sb2, text="Disconnected", bg=BG,
                                 font=FONT_NORM, anchor="w")
        self.lbl_stat.pack(side="left", fill="x", expand=True)
        self.lbl_cmds = tk.Label(sb2, text="", bg=BG, font=FONT_NORM)
        self.lbl_cmds.pack(side="right", padx=4)

    def _noop(self):
        pass

    def _about(self):
        messagebox.showinfo("JewAIXP",
                            "ICQ-style client v1.0\n"
                            "council_chat 8770\n"
                            "Python 3.4 + tkinter\n\nDixi. 3D.")

    # ---- data ----
    def refresh_channels(self):
        r = self.api.state()
        keys = ["ALL"]
        if r.get("ok"):
            ch = r["data"].get("channels") or {}
            for k in sorted(ch.keys()):
                keys.append(k)
        self.channels = keys
        self._rebuild_list()

    def _base_kind(self, ch, ch_info):
        if ch == "ALL":
            return "online"
        info = ch_info.get(ch) or {}
        return "online" if info.get("agent_ping") else "offline"

    def _display_name(self, ch):
        return CH_NAMES.get(ch, ch)

    def _rebuild_list(self):
        self.contacts.configure(state="normal")
        self.contacts.delete("1.0", "end")
        self.rows = {}

        flt = self.search.get().strip().lower()
        ch_info = {}
        rs = self.api.status()
        if rs.get("ok"):
            ch_info = rs["data"].get("channels") or {}

        for ch in self.channels:
            name = self._display_name(ch)
            if flt and flt not in name.lower():
                continue

            base_kind = self._base_kind(ch, ch_info)
            is_online = (base_kind == "online")
            unread = self.state.unread(ch)
            bold = bool(unread > 0 and (ch == "ALL" or is_online))

            img = self.icons.get(base_kind, "normal")

            row_start = self.contacts.index("end-1c")
            img_id = self.contacts.image_create("end", image=img, padx=2, pady=1)
            name_start = self.contacts.index("end-1c")
            self.contacts.insert("end", " " + name)
            name_end = self.contacts.index("end-1c")
            self.contacts.insert("end", "\n")
            row_end = self.contacts.index("end-1c")

            tag = "row_" + ch
            self.contacts.tag_add(tag, row_start, row_end)

            # remember line number for dbl-click handling
            line_num = int(self.contacts.index(row_start).split(".")[0])
            self.rows[ch] = {"image": img_id, "base": base_kind,
                             "tag": tag, "open": False, "bold": bold,
                             "line": line_num,
                             "name_start": name_start, "name_end": name_end}
        # Tkinter: tag priority is FIFO by creation. Raise bold/norm above row tags.
        try:
            self.contacts.tag_raise("bold")
            self.contacts.tag_raise("norm")
        except Exception:
            pass
        self.contacts.configure(state="disabled")

    def _line_of_event(self, evt):
        try:
            idx = self.contacts.index("@%d,%d" % (evt.x, evt.y))
            return int(idx.split(".")[0])
        except Exception:
            return -1

    def _ch_at_line(self, line):
        for ch, info in self.rows.items():
            if info.get("line") == line:
                return ch
        return None

    def _on_text_click(self, evt):
        line = self._line_of_event(evt)
        ch = self._ch_at_line(line)
        if ch:
            self._on_click(ch)
        return "break"

    def _on_text_dbl(self, evt):
        line = self._line_of_event(evt)
        ch = self._ch_at_line(line)
        if ch:
            self._on_dbl(ch)
        return "break"

    def _update_bold(self, ch):
        info = self.rows.get(ch)
        if not info:
            return
        try:
            unread = self.state.unread(ch) > 0
            base = info.get("base", "offline")
            want_bold = bool(unread and (ch == "ALL" or base == "online"))
            if want_bold == info.get("bold", False):
                return
            info["bold"] = want_bold
            ns = info.get("name_start")
            ne = info.get("name_end")
            if ns and ne:
                self.contacts.tag_remove("bold", ns, ne)
                self.contacts.tag_remove("norm", ns, ne)
                self.contacts.tag_add("bold" if want_bold else "norm", ns, ne)
                self.contacts.tag_raise("bold")
                self.contacts.tag_raise("norm")
        except Exception:
            pass

    def on_council(self):
        r = self.api.meeting_on(True)
        self._flash_status("COUNCIL ON", r)

    def on_pause_all(self):
        r = self.api.pause_all(True)
        self._flash_status("PAUSE-ALL", r)

    def on_resume(self):
        r = self.api.pause_all(False)
        if r.get("ok"):
            self.api.meeting_on(False)
        self._flash_status("RESUME", r)

    def on_logs(self):
        import ui_chat
        ui_chat.HistoryWindow(self.root, self.api, "ALL", "Logs - chat")

    def _flash_status(self, what, result):
        ok = result.get("ok")
        msg = what + (" ok" if ok else " FAIL")
        try:
            self.lbl_stat.configure(text=msg)
        except Exception:
            pass

    def _toggle_sound(self):
        self._sound_on = not getattr(self, "_sound_on", True)
        sound.set_enabled(self._sound_on)
        try:
            self.lbl_stat.configure(text="sound " + ("on" if self._sound_on else "off"))
        except Exception:
            pass

    def _set_icon(self, ch, kind):
        info = self.rows.get(ch)
        if not info:
            return
        try:
            self.contacts.configure(state="normal")
            self.contacts.image_configure(info["image"],
                                          image=self.icons.get(kind, "normal"))
            self.contacts.configure(state="disabled")
        except Exception:
            pass

    def _on_click(self, ch):
        for k, v in self.rows.items():
            self.contacts.tag_configure(v["tag"],
                                        background=(SEL_BG if k == ch else BG),
                                        foreground=(SEL_FG if k == ch else "black"))

    def _on_dbl(self, ch):
        if ch in self.rows:
            self.rows[ch]["open"] = True
        self.state.unread_count[ch] = 0
        self.state.save()
        if ch in self.rows:
            self._set_icon(ch, self.rows[ch]["base"])
        self.on_open_chat(ch)

    def notify_chat_closed(self, ch):
        if ch in self.rows:
            self.rows[ch]["open"] = False

    def set_connection(self, connected, text=""):
        kind = "online" if connected else "offline"
        self.ico_stat = self.icons.get(kind, "normal")
        self.lbl_stat_icon.configure(image=self.ico_stat)
        self.lbl_stat.configure(text=text or ("Connected" if connected else "Disconnected"))

    # ---- blink ----
    def _schedule_blink(self):
        self.root.after(600, self._blink_tick)

    def _blink_tick(self):
        self.blink_on = not self.blink_on
        for ch, info in list(self.rows.items()):
            if info.get("open"):
                continue
            if self.state.unread(ch) <= 0:
                continue
            kind = "new" if self.blink_on else info["base"]
            self._set_icon(ch, kind)
        self._schedule_blink()

    # ---- poll ----
    def _schedule_poll(self):
        self.root.after(int(self.cfg.get("poll_ms", 4000)), self._poll_tick)

    def _poll_tick(self):
        try:
            self._refresh_unread()
        except Exception:
            pass
        self._schedule_poll()

    def _refresh_unread(self):
        r = self.api.state()
        connected = bool(r.get("ok"))
        self.set_connection(connected, self.cfg.get("server", ""))
        if not connected:
            return

        prev_total = self.state.total_unread()
        rm = self.api.messages_all()
        if rm.get("ok"):
            data = rm["data"]
            msgs = data if isinstance(data, list) else (data.get("messages") or [])
            self.state.unread_count["ALL"] = self.state.count_new("ALL", msgs)

        for ch in self.channels:
            if ch == "ALL":
                continue
            rc = self.api.chat(ch)
            if rc.get("ok"):
                msgs = rc["data"].get("messages") or []
                self.state.unread_count[ch] = self.state.count_new(ch, msgs)

        # play sound if total unread grew
        try:
            if self.state.total_unread() > prev_total:
                sound.message()
        except Exception:
            pass

        rs = self.api.status()
        ch_info = {}
        if rs.get("ok"):
            data = rs["data"]
            ch_info = data.get("channels") or {}
            # cmds_from_start: aggregate or per-channel, take max
            try:
                cmds = None
                if isinstance(data.get("cmds_from_start"), int):
                    cmds = data.get("cmds_from_start")
                else:
                    vals = []
                    for k in ch_info:
                        v = ch_info[k].get("cmds_from_start")
                        if isinstance(v, int):
                            vals.append(v)
                    if vals:
                        cmds = max(vals)
                if cmds is not None:
                    self.lbl_cmds.configure(text="cmds:" + str(cmds))
                    if cmds >= 850:
                        self.lbl_cmds.configure(fg="#e00000")
                    elif cmds >= 700:
                        self.lbl_cmds.configure(fg="#c08000")
                    else:
                        self.lbl_cmds.configure(fg="#000080")
            except Exception:
                pass

        for ch, info in list(self.rows.items()):
            info["base"] = self._base_kind(ch, ch_info)
            self._update_bold(ch)
            if info.get("open"):
                self._set_icon(ch, info["base"])
                continue
            if self.state.unread(ch) > 0:
                continue
            self._set_icon(ch, info["base"])