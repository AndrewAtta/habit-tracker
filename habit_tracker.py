#!/usr/bin/env python3
"""Simple Linux desktop habit tracker with a calendar view."""

import tkinter as tk
from tkinter import font as tkfont
import json
import os
import calendar
from datetime import datetime

DATA_FILE = os.path.expanduser("~/.habit_tracker_data.json")

HABITS = [
    "Exercise",
    "Read for 30 minutes",
    "Meditate",
    "Drink 8 glasses of water",
    "Sleep 8 hours",
]

# Color palette
BG_DARK       = "#1e1e2e"
BG_PANEL      = "#2a2a3e"
BG_HEADER     = "#12121e"
TEXT_LIGHT    = "#e0e0f0"
TEXT_DIM      = "#888899"
ACCENT        = "#7c6af7"
COLOR_NONE    = "#c0392b"   # 0/5  — red
COLOR_PARTIAL = "#e67e22"   # 1-4  — orange
COLOR_DONE    = "#27ae60"   # 5/5  — green
COLOR_FUTURE  = "#3a3a52"   # future days — neutral dark
DAY_NAMES     = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def day_color(completed: int, is_future: bool) -> str:
    if is_future:
        return COLOR_FUTURE
    if completed == 0:
        return COLOR_NONE
    if completed == len(HABITS):
        return COLOR_DONE
    return COLOR_PARTIAL


class DayDialog(tk.Toplevel):
    """Modal dialog showing the 5 habits for a given day."""

    def __init__(self, parent, date_key: str, day_label: str, data: dict, on_close):
        super().__init__(parent)
        self.title(day_label)
        self.resizable(False, False)
        self.configure(bg=BG_PANEL)
        self.grab_set()  # modal

        self.date_key = date_key
        self.data = data
        self.on_close = on_close

        self._build(day_label)

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self, day_label: str):
        pad = dict(padx=24, pady=8)

        tk.Label(
            self, text=day_label, bg=BG_PANEL, fg=TEXT_LIGHT,
            font=("Sans", 15, "bold"),
        ).pack(pady=(18, 4))

        tk.Label(
            self, text="Check off the habits you completed today:",
            bg=BG_PANEL, fg=TEXT_DIM, font=("Sans", 10),
        ).pack(**pad)

        sep = tk.Frame(self, bg=ACCENT, height=1)
        sep.pack(fill=tk.X, padx=24, pady=4)

        day_data = self.data.get(self.date_key, {})
        self.vars: list[tk.BooleanVar] = []

        for habit in HABITS:
            var = tk.BooleanVar(value=bool(day_data.get(habit, False)))
            self.vars.append(var)

            row = tk.Frame(self, bg=BG_PANEL)
            row.pack(fill=tk.X, padx=24, pady=3)

            cb = tk.Checkbutton(
                row, variable=var, bg=BG_PANEL, activebackground=BG_PANEL,
                selectcolor=ACCENT, fg=TEXT_LIGHT, activeforeground=TEXT_LIGHT,
                font=("Sans", 11), text=habit, anchor="w",
                command=self._save,
                cursor="hand2",
            )
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)

        sep2 = tk.Frame(self, bg="#444455", height=1)
        sep2.pack(fill=tk.X, padx=24, pady=(12, 0))

        btn = tk.Button(
            self, text="Done", command=self._close,
            bg=ACCENT, fg="white", activebackground="#5a4acc",
            activeforeground="white", relief=tk.FLAT,
            font=("Sans", 11, "bold"), cursor="hand2",
            padx=28, pady=6,
        )
        btn.pack(pady=14)

    def _save(self):
        day_data = {habit: var.get() for habit, var in zip(HABITS, self.vars)}
        self.data[self.date_key] = day_data
        save_data(self.data)
        self.on_close()   # refresh calendar

    def _close(self):
        self._save()
        self.destroy()


class HabitTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Habit Tracker")
        self.configure(bg=BG_DARK)
        self.minsize(640, 520)

        self.data = load_data()
        now = datetime.now()
        self.year  = now.year
        self.month = now.month
        self.today = now.date()

        self._build_header()
        self._build_day_names()
        self.grid_frame = tk.Frame(self, bg=BG_DARK)
        self.grid_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self._draw_calendar()

    # ------------------------------------------------------------------ header

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_HEADER)
        hdr.pack(fill=tk.X)

        btn_cfg = dict(bg=BG_HEADER, fg=TEXT_LIGHT, activebackground=BG_PANEL,
                       activeforeground=TEXT_LIGHT, relief=tk.FLAT,
                       font=("Sans", 14, "bold"), cursor="hand2", padx=14, pady=10)

        tk.Button(hdr, text="‹", command=self._prev_month, **btn_cfg).pack(side=tk.LEFT)
        tk.Button(hdr, text="›", command=self._next_month, **btn_cfg).pack(side=tk.RIGHT)

        self.month_label = tk.Label(
            hdr, bg=BG_HEADER, fg=TEXT_LIGHT,
            font=("Sans", 14, "bold"),
        )
        self.month_label.pack(side=tk.LEFT, expand=True)
        self._update_month_label()

    def _update_month_label(self):
        self.month_label.config(
            text=datetime(self.year, self.month, 1).strftime("%B %Y")
        )

    # ------------------------------------------------------------ day-name row

    def _build_day_names(self):
        row = tk.Frame(self, bg=BG_DARK)
        row.pack(fill=tk.X, padx=16, pady=(10, 4))
        for i, name in enumerate(DAY_NAMES):
            row.columnconfigure(i, weight=1)
            tk.Label(
                row, text=name, bg=BG_DARK, fg=TEXT_DIM,
                font=("Sans", 9, "bold"), anchor="center",
            ).grid(row=0, column=i, sticky="ew")

    # --------------------------------------------------------------- calendar

    def _draw_calendar(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        for col in range(7):
            self.grid_frame.columnconfigure(col, weight=1, uniform="col")

        weeks = calendar.monthcalendar(self.year, self.month)
        for row_idx, week in enumerate(weeks):
            self.grid_frame.rowconfigure(row_idx, weight=1, uniform="row")
            for col_idx, day in enumerate(week):
                if day == 0:
                    tk.Frame(self.grid_frame, bg=BG_DARK).grid(
                        row=row_idx, column=col_idx, sticky="nsew", padx=3, pady=3
                    )
                    continue

                date_key   = f"{self.year}-{self.month:02d}-{day:02d}"
                from datetime import date as date_type
                cell_date  = date_type(self.year, self.month, day)
                is_future  = cell_date > self.today
                day_data   = self.data.get(date_key, {})
                completed  = sum(1 for h in HABITS if day_data.get(h, False))
                bg         = day_color(completed, is_future)

                is_today = (cell_date == self.today)
                border   = ACCENT if is_today else bg

                cell = tk.Frame(
                    self.grid_frame, bg=border,
                    highlightbackground=border, highlightthickness=2,
                )
                cell.grid(row=row_idx, column=col_idx, sticky="nsew", padx=3, pady=3)

                inner = tk.Frame(cell, bg=bg)
                inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

                # Day number
                num_font = ("Sans", 11, "bold") if is_today else ("Sans", 11)
                tk.Label(
                    inner, text=str(day), bg=bg,
                    fg="white", font=num_font, anchor="nw",
                ).pack(anchor="nw", padx=6, pady=(4, 0))

                # Progress indicator
                prog_text = f"{completed}/{len(HABITS)}" if not is_future else ""
                tk.Label(
                    inner, text=prog_text, bg=bg,
                    fg="white", font=("Sans", 8), anchor="se",
                ).pack(anchor="se", padx=6, pady=(0, 4))

                # Click binding — capture date_key and day
                for widget in (cell, inner) + tuple(inner.winfo_children()):
                    widget.bind("<Button-1>", lambda e, dk=date_key, d=day: self._open_day(dk, d))
                    if not is_future:
                        widget.config(cursor="hand2")

    # --------------------------------------------------- navigation & opening

    def _prev_month(self):
        if self.month == 1:
            self.month, self.year = 12, self.year - 1
        else:
            self.month -= 1
        self._update_month_label()
        self._draw_calendar()

    def _next_month(self):
        if self.month == 12:
            self.month, self.year = 1, self.year + 1
        else:
            self.month += 1
        self._update_month_label()
        self._draw_calendar()

    def _open_day(self, date_key: str, day: int):
        label = datetime(self.year, self.month, day).strftime("%A, %B %-d %Y")
        DayDialog(self, date_key, label, self.data, on_close=self._draw_calendar)


if __name__ == "__main__":
    app = HabitTracker()
    app.mainloop()
