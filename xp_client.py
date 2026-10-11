# -*- coding: utf-8 -*-
# JewAIXP ICQ-style client. Python 3.4 compatible.
# Entry point: builds main window, manages chat dialogs.

import os
import io
import json
import sys

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    import Tkinter as tk
    import tkMessageBox as messagebox

import api as api_mod
import state as st_mod
import ui_main
import ui_chat


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xp_client.json")
DEFAULTS = {
    "server": "http://127.0.0.1:8770",
    "nick": "operator",
    "poll_ms": 4000,
    "font_size": 9
}


def load_config():
    cfg = dict(DEFAULTS)
    if os.path.isfile(CONFIG_FILE):
        try:
            f = io.open(CONFIG_FILE, "r", encoding="utf-8")
            try:
                data = json.load(f)
                for k in data:
                    cfg[k] = data[k]
            finally:
                f.close()
        except Exception:
            pass
    return cfg


def save_config(cfg):
    try:
        f = io.open(CONFIG_FILE, "w", encoding="utf-8")
        try:
            f.write(json.dumps(cfg, ensure_ascii=False, indent=2))
        finally:
            f.close()
    except Exception:
        pass


class Client(object):
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.api = api_mod.Api(self.cfg["server"], self.cfg["nick"])
        self.state = st_mod.State()
        self.open_chats = {}     # ch -> ChatWindow
        self.main = None
        self._build_main()

    def _build_main(self):
        self.main = ui_main.MainWindow(
            root=self.root,
            api=self.api,
            cfg=self.cfg,
            on_open_chat=self.open_chat,
            on_settings=self.open_settings,
            on_pause_all=self.pause_all
        )
        # sync state object with main window's
        self.main.state = self.state

    # ------------- chat windows -------------
    def open_chat(self, ch):
        if ch in self.open_chats:
            try:
                self.open_chats[ch].win.lift()
                self.open_chats[ch].win.focus_force()
            except Exception:
                pass
            return
        label = self.main._display_name(ch)
        w = ui_chat.ChatWindow(
            root=self.root,
            api=self.api,
            state=self.state,
            ch=ch,
            label=label,
            nick=self.cfg["nick"],
            on_close=self._on_chat_close
        )
        self.open_chats[ch] = w

    def _on_chat_close(self, ch):
        self.open_chats.pop(ch, None)
        try:
            self.main.notify_chat_closed(ch)
        except Exception:
            pass

    # ------------- settings -------------
    def open_settings(self):
        w = tk.Toplevel(self.root)
        w.title("\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438")
        w.configure(bg="#c0c0c0")
        w.geometry("400x220")
        w.transient(self.root)
        w.grab_set()

        tk.Label(w, text="\u0421\u0435\u0440\u0432\u0435\u0440 (URL):", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).grid(row=0, column=0, sticky="w", padx=8, pady=8)
        e_srv = tk.Entry(w, width=40, bd=2, relief="sunken")
        e_srv.insert(0, self.cfg["server"])
        e_srv.grid(row=0, column=1, sticky="we", padx=8, pady=8)

        tk.Label(w, text="\u041d\u0438\u043a:", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).grid(row=1, column=0, sticky="w", padx=8, pady=4)
        e_nick = tk.Entry(w, width=40, bd=2, relief="sunken")
        e_nick.insert(0, self.cfg["nick"])
        e_nick.grid(row=1, column=1, sticky="we", padx=8, pady=4)

        tk.Label(w, text="Poll, ms:", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).grid(row=2, column=0, sticky="w", padx=8, pady=4)
        e_poll = tk.Entry(w, width=40, bd=2, relief="sunken")
        e_poll.insert(0, str(self.cfg.get("poll_ms", 4000)))
        e_poll.grid(row=2, column=1, sticky="we", padx=8, pady=4)

        def do_save():
            self.cfg["server"] = e_srv.get().strip() or DEFAULTS["server"]
            self.cfg["nick"] = e_nick.get().strip() or DEFAULTS["nick"]
            try:
                self.cfg["poll_ms"] = int(e_poll.get().strip() or "4000")
            except Exception:
                self.cfg["poll_ms"] = 4000
            save_config(self.cfg)
            self.api.set_base(self.cfg["server"])
            self.api.set_nick(self.cfg["nick"])
            self.main.cfg = self.cfg
            self.main.refresh_channels()
            self.main.set_connection(True, self.cfg["server"])
            w.destroy()

        tk.Button(w, text="\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", width=12,
                  command=do_save, bd=1, relief="raised", bg="#c0c0c0",
                  font=("MS Sans Serif", 8)).grid(row=3, column=1, sticky="e", padx=8, pady=12)

    # ------------- service -------------
    def pause_all(self):
        if not messagebox.askyesno("PAUSE-ALL",
                                   "\u041f\u043e\u043b\u043d\u0430\u044f \u043f\u0430\u0443\u0437\u0430 \u0432\u0441\u0435\u043c \u0430\u0433\u0435\u043d\u0442\u0430\u043c. \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c?"):
            return
        r = self.api.pause_all(True)
        if r.get("ok"):
            messagebox.showinfo("PAUSE-ALL", "\u041e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e.")
        else:
            messagebox.showerror("PAUSE-ALL", str(r.get("error"))[:200])


def main():
    root = tk.Tk()
    app = Client(root)
    root.mainloop()


if __name__ == "__main__":
    main()