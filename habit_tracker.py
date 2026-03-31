#!/usr/bin/env python3
"""Simple Linux desktop habit tracker with a calendar + side-panel layout."""

import tkinter as tk
import json
import os
import calendar
from datetime import datetime, date

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
COLOR_FUTURE  = "#3a3a52"   # future days — neutral
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


class HabitTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Habit Tracker")
        self.configure(bg=BG_DARK)
        self.minsize(820, 540)

        self.data = load_data()
        now = datetime.now()
        self.year  = now.year
        self.month = now.month
        self.today = date.today()

        # Currently selected day (date_key string or None)
        self.selected_key: str | None = None
        self.habit_vars: list[tk.BooleanVar] = []

        self._build_header()

        # Main body: calendar area (left) + side panel (right)
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True)

        # Left: day-name row + calendar grid
        left = tk.Frame(body, bg=BG_DARK)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 8), pady=(10, 16))

        self._build_day_names(left)

        self.grid_frame = tk.Frame(left, bg=BG_DARK)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

        # Right: side panel (fixed width)
        self.side_panel = tk.Frame(body, bg=BG_PANEL, width=220)
        self.side_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 16), pady=(10, 16))
        self.side_panel.pack_propagate(False)
        self._build_side_panel_placeholder()

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

        self.month_label = tk.Label(hdr, bg=BG_HEADER, fg=TEXT_LIGHT,
                                    font=("Sans", 14, "bold"))
        self.month_label.pack(side=tk.LEFT, expand=True)
        self._update_month_label()

    def _update_month_label(self):
        self.month_label.config(
            text=datetime(self.year, self.month, 1).strftime("%B %Y")
        )

    # ------------------------------------------------------------ day-name row

    def _build_day_names(self, parent):
        row = tk.Frame(parent, bg=BG_DARK)
        row.pack(fill=tk.X, pady=(0, 4))
        for i, name in enumerate(DAY_NAMES):
            row.columnconfigure(i, weight=1)
            tk.Label(row, text=name, bg=BG_DARK, fg=TEXT_DIM,
                     font=("Sans", 9, "bold"), anchor="center",
                     ).grid(row=0, column=i, sticky="ew")

    # --------------------------------------------------------------- side panel

    def _clear_side_panel(self):
        for w in self.side_panel.winfo_children():
            w.destroy()
        self.habit_vars = []

    def _build_side_panel_placeholder(self):
        self._clear_side_panel()
        tk.Label(self.side_panel, text="Select a day",
                 bg=BG_PANEL, fg=TEXT_DIM, font=("Sans", 11),
                 wraplength=180, justify="center",
                 ).place(relx=0.5, rely=0.5, anchor="center")

    def _build_side_panel(self, date_key: str, day: int):
        self._clear_side_panel()
        self.selected_key = date_key

        label = datetime(self.year, self.month, day).strftime("%A\n%-d %B %Y")
        tk.Label(self.side_panel, text=label, bg=BG_PANEL, fg=TEXT_LIGHT,
                 font=("Sans", 12, "bold"), justify="center",
                 ).pack(pady=(18, 6))

        tk.Frame(self.side_panel, bg=ACCENT, height=1).pack(fill=tk.X, padx=16, pady=(0, 10))

        day_data = self.data.get(date_key, {})

        for habit in HABITS:
            var = tk.BooleanVar(value=bool(day_data.get(habit, False)))
            self.habit_vars.append(var)

            cb = tk.Checkbutton(
                self.side_panel, variable=var, text=habit,
                bg=BG_PANEL, activebackground=BG_PANEL,
                selectcolor=BG_DARK,
                fg=TEXT_LIGHT, activeforeground=TEXT_LIGHT,
                font=("Sans", 10), anchor="w", wraplength=180,
                justify="left", cursor="hand2",
                command=self._on_habit_toggle,
            )
            cb.pack(fill=tk.X, padx=14, pady=4)

    def _on_habit_toggle(self):
        if self.selected_key is None:
            return
        day_data = {h: v.get() for h, v in zip(HABITS, self.habit_vars)}
        self.data[self.selected_key] = day_data
        save_data(self.data)
        self._draw_calendar()   # refresh cell colours

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
                        row=row_idx, column=col_idx, sticky="nsew", padx=3, pady=3)
                    continue

                date_key  = f"{self.year}-{self.month:02d}-{day:02d}"
                cell_date = date(self.year, self.month, day)
                is_future = cell_date > self.today
                day_data  = self.data.get(date_key, {})
                completed = sum(1 for h in HABITS if day_data.get(h, False))
                bg        = day_color(completed, is_future)

                is_today    = (cell_date == self.today)
                is_selected = (date_key == self.selected_key)
                border = ACCENT if (is_today or is_selected) else bg

                cell = tk.Frame(self.grid_frame, bg=border,
                                highlightbackground=border, highlightthickness=2)
                cell.grid(row=row_idx, column=col_idx, sticky="nsew", padx=3, pady=3)

                inner = tk.Frame(cell, bg=bg)
                inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

                num_font = ("Sans", 11, "bold") if is_today else ("Sans", 11)
                tk.Label(inner, text=str(day), bg=bg, fg="white",
                         font=num_font, anchor="nw",
                         ).pack(anchor="nw", padx=6, pady=(4, 0))

                prog_text = f"{completed}/{len(HABITS)}" if not is_future else ""
                tk.Label(inner, text=prog_text, bg=bg, fg="white",
                         font=("Sans", 8), anchor="se",
                         ).pack(anchor="se", padx=6, pady=(0, 4))

                if not is_future:
                    for widget in (cell, inner) + tuple(inner.winfo_children()):
                        widget.bind("<Button-1>",
                                    lambda e, dk=date_key, d=day: self._select_day(dk, d))
                        widget.config(cursor="hand2")

    # --------------------------------------------------- navigation & selection

    def _prev_month(self):
        if self.month == 1:
            self.month, self.year = 12, self.year - 1
        else:
            self.month -= 1
        self.selected_key = None
        self._build_side_panel_placeholder()
        self._update_month_label()
        self._draw_calendar()

    def _next_month(self):
        if self.month == 12:
            self.month, self.year = 1, self.year + 1
        else:
            self.month += 1
        self.selected_key = None
        self._build_side_panel_placeholder()
        self._update_month_label()
        self._draw_calendar()

    def _select_day(self, date_key: str, day: int):
        self._build_side_panel(date_key, day)
        self._draw_calendar()   # re-draw so selected highlight updates


if __name__ == "__main__":
    app = HabitTracker()
    app.mainloop()
