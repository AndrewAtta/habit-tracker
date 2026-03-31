#!/usr/bin/env python3
"""Habit Tracker — modern dark UI with editable habits."""

import tkinter as tk
import json, os, calendar
from datetime import datetime, date

# ── persistence ───────────────────────────────────────────────────────────────
DATA_FILE = os.path.expanduser("~/.habit_tracker_data.json")

DEFAULT_HABITS = [
    "Exercise",
    "Read for 30 minutes",
    "Meditate",
    "Drink 8 glasses of water",
    "Sleep 8 hours",
]

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            raw = json.load(f)
        # migrate old format (dict-of-dicts keyed by habit name → index arrays)
        if raw and "habits" not in raw:
            habits = list(DEFAULT_HABITS)
            days = {
                dk: [bool(dv.get(h, False)) for h in habits]
                for dk, dv in raw.items()
                if isinstance(dv, dict)
            }
            return {"habits": habits, "days": days}
        return raw
    return {"habits": list(DEFAULT_HABITS), "days": {}}

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── palette ───────────────────────────────────────────────────────────────────
BG         = "#0d0d1a"
SURFACE    = "#13131f"
SURFACE2   = "#1a1a2e"
BORDER     = "#252538"
TEXT       = "#e2e2f0"
TEXT_MUTED = "#5a5a7a"
ACCENT     = "#7c6af7"
RED        = "#d95f5f"
ORANGE     = "#d4874a"
GREEN      = "#3db870"
NEUTRAL    = "#252538"

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ── drawing helper ────────────────────────────────────────────────────────────
def _rrect(cv: tk.Canvas, x: int, y: int, w: int, h: int, r: int, fill: str):
    """Draw a filled rounded rectangle on a canvas."""
    x2, y2 = x + w, y + h
    # four corner arcs
    cv.create_arc(x,    y,    x+2*r, y+2*r, start=90,  extent=90, fill=fill, outline=fill)
    cv.create_arc(x2-2*r, y, x2,   y+2*r,  start=0,   extent=90, fill=fill, outline=fill)
    cv.create_arc(x,  y2-2*r, x+2*r, y2,   start=180, extent=90, fill=fill, outline=fill)
    cv.create_arc(x2-2*r, y2-2*r, x2, y2,  start=270, extent=90, fill=fill, outline=fill)
    # fill body
    cv.create_rectangle(x+r, y,   x2-r, y2,   fill=fill, outline=fill)
    cv.create_rectangle(x,   y+r, x2,   y2-r, fill=fill, outline=fill)

def _dim(hex_color: str) -> str:
    """Return a darkened version of a hex color (for empty progress dots)."""
    try:
        r = int(int(hex_color[1:3], 16) * 0.45)
        g = int(int(hex_color[3:5], 16) * 0.45)
        b = int(int(hex_color[5:7], 16) * 0.45)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#222233"

def cell_color(completed: int, n: int, is_future: bool) -> str:
    if is_future:   return NEUTRAL
    if completed == 0: return RED
    if completed == n: return GREEN
    return ORANGE

# ── calendar cell (canvas-based for rounded corners) ─────────────────────────
class DayCell(tk.Canvas):
    R = 10  # corner radius

    def __init__(self, parent, day, date_key, is_today, is_future,
                 completed, n_habits, on_click):
        super().__init__(parent, bg=BG, highlightthickness=0,
                         cursor="arrow" if is_future else "hand2")
        self.day       = day
        self.date_key  = date_key
        self.is_today  = is_today
        self.is_future = is_future
        self.completed = completed
        self.n_habits  = n_habits
        self.selected  = False

        if not is_future:
            self.bind("<Button-1>", lambda e: on_click(date_key, day))
        self.bind("<Configure>", lambda e: self._draw())

    def refresh(self, completed: int, selected: bool):
        self.completed = completed
        self.selected  = selected
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 6 or h < 6:
            return

        fill = cell_color(self.completed, self.n_habits, self.is_future)
        highlighted = self.is_today or self.selected

        if highlighted:
            _rrect(self, 0, 0, w, h, self.R, ACCENT)
            _rrect(self, 3, 3, w - 6, h - 6, self.R - 2, fill)
        else:
            _rrect(self, 0, 0, w, h, self.R, fill)

        # Day number
        weight = "bold" if self.is_today else "normal"
        self.create_text(10, 8, text=str(self.day),
                         fill=TEXT, font=("Helvetica Neue", 11, weight), anchor="nw")

        # Progress dots
        if not self.is_future and self.n_habits > 0:
            dr, gap = 3, 4
            total_w = self.n_habits * dr * 2 + (self.n_habits - 1) * gap
            x0 = max(8, (w - total_w) // 2)
            y0 = h - 12
            for i in range(self.n_habits):
                x = x0 + i * (dr * 2 + gap)
                dot = TEXT if i < self.completed else _dim(fill)
                self.create_oval(x, y0, x + dr * 2, y0 + dr * 2,
                                 fill=dot, outline="")

# ── habit row in the side panel ───────────────────────────────────────────────
class HabitRow(tk.Frame):
    def __init__(self, parent, text: str, checked: bool, on_toggle):
        super().__init__(parent, bg=SURFACE2, cursor="hand2")
        self.checked    = checked
        self._on_toggle = on_toggle

        self._cv = tk.Canvas(self, width=20, height=20,
                             bg=SURFACE2, highlightthickness=0)
        self._cv.pack(side=tk.LEFT, padx=(16, 10), pady=13)
        self._draw_check()

        self._lbl = tk.Label(self, text=text, bg=SURFACE2, fg=TEXT,
                             font=("Helvetica Neue", 10), anchor="w",
                             wraplength=160, justify="left")
        self._lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

        for w in (self, self._cv, self._lbl):
            w.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        self.checked = not self.checked
        self._draw_check()
        self._on_toggle()

    def _draw_check(self):
        self._cv.delete("all")
        if self.checked:
            self._cv.create_oval(1, 1, 19, 19, fill=ACCENT, outline=ACCENT)
            # checkmark
            self._cv.create_line(5, 10, 8, 14, 15, 5,
                                 fill="white", width=2,
                                 capstyle="round", joinstyle="round")
        else:
            self._cv.create_oval(1, 1, 19, 19, fill="", outline=BORDER, width=2)

# ── main application ──────────────────────────────────────────────────────────
class HabitTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Habit Tracker")
        self.configure(bg=BG)
        self.minsize(860, 560)

        self._raw   = load_data()
        self.habits: list = self._raw.setdefault("habits", list(DEFAULT_HABITS))
        self.days:   dict = self._raw.setdefault("days",   {})

        now = datetime.now()
        self.year, self.month = now.year, now.month
        self.today            = date.today()
        self.selected_key: str | None = None
        self._panel_mode      = "placeholder"
        self.cell_map: dict[str, DayCell] = {}

        self._build_ui()

    # ── layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()

        body = tk.Frame(self, bg=BG)
        body.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(body, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                  padx=(16, 6), pady=(8, 16))
        self._build_day_labels(left)
        self.grid_frame = tk.Frame(left, bg=BG)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

        self.panel = tk.Frame(body, bg=SURFACE2, width=248)
        self.panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 16), pady=(8, 16))
        self.panel.pack_propagate(False)
        self._show_placeholder()

        self._draw_calendar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=SURFACE)
        hdr.pack(fill=tk.X)
        tk.Frame(hdr, bg=ACCENT, height=2).pack(fill=tk.X)

        inner = tk.Frame(hdr, bg=SURFACE)
        inner.pack(fill=tk.X, padx=16, pady=8)

        nav = dict(bg=SURFACE, fg=TEXT_MUTED, activebackground=SURFACE2,
                   activeforeground=TEXT, relief=tk.FLAT,
                   font=("Helvetica Neue", 16), cursor="hand2",
                   padx=10, pady=2, borderwidth=0)
        tk.Button(inner, text="‹", command=self._prev_month, **nav).pack(side=tk.LEFT)
        tk.Button(inner, text="›", command=self._next_month, **nav).pack(side=tk.LEFT, padx=(4, 0))

        self.month_lbl = tk.Label(inner, bg=SURFACE, fg=TEXT,
                                  font=("Helvetica Neue", 14, "bold"))
        self.month_lbl.pack(side=tk.LEFT, padx=14)
        self._update_month_lbl()

        tk.Button(inner, text="⚙", command=self._toggle_settings,
                  bg=SURFACE, fg=TEXT_MUTED, activebackground=SURFACE2,
                  activeforeground=TEXT, relief=tk.FLAT,
                  font=("Helvetica Neue", 14), cursor="hand2",
                  padx=10, pady=2, borderwidth=0).pack(side=tk.RIGHT)

    def _update_month_lbl(self):
        self.month_lbl.config(
            text=datetime(self.year, self.month, 1).strftime("%B %Y"))

    def _build_day_labels(self, parent):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill=tk.X, pady=(0, 6))
        for i, name in enumerate(DAY_NAMES):
            row.columnconfigure(i, weight=1)
            tk.Label(row, text=name, bg=BG, fg=TEXT_MUTED,
                     font=("Helvetica Neue", 9, "bold"), anchor="center",
                     ).grid(row=0, column=i, sticky="ew")

    # ── side panel: placeholder ───────────────────────────────────────────────
    def _clear_panel(self):
        for w in self.panel.winfo_children():
            w.destroy()

    def _show_placeholder(self):
        self._clear_panel()
        self._panel_mode = "placeholder"
        tk.Label(self.panel, text="Select a day\nto track habits",
                 bg=SURFACE2, fg=TEXT_MUTED,
                 font=("Helvetica Neue", 11), justify="center",
                 ).place(relx=0.5, rely=0.5, anchor="center")

    # ── side panel: day view ──────────────────────────────────────────────────
    def _show_day_panel(self, date_key: str, day: int):
        self._clear_panel()
        self._panel_mode = "day"
        self.selected_key = date_key

        dt     = datetime(self.year, self.month, day)
        checks = list(self.days.get(date_key, []))
        while len(checks) < len(self.habits):
            checks.append(False)

        tk.Label(self.panel, text=dt.strftime("%A"),
                 bg=SURFACE2, fg=TEXT_MUTED,
                 font=("Helvetica Neue", 10)).pack(pady=(20, 0))
        tk.Label(self.panel, text=dt.strftime("%-d %B %Y"),
                 bg=SURFACE2, fg=TEXT,
                 font=("Helvetica Neue", 13, "bold")).pack(pady=(2, 14))
        tk.Frame(self.panel, bg=BORDER, height=1).pack(fill=tk.X, padx=0)

        self._habit_rows: list[HabitRow] = []
        for i, (habit, checked) in enumerate(zip(self.habits, checks)):
            row = HabitRow(self.panel, habit, bool(checked), self._on_toggle)
            row.pack(fill=tk.X)
            self._habit_rows.append(row)
            if i < len(self.habits) - 1:
                tk.Frame(self.panel, bg=BORDER, height=1).pack(fill=tk.X, padx=16)

    def _on_toggle(self):
        if self.selected_key is None:
            return
        self.days[self.selected_key] = [row.checked for row in self._habit_rows]
        save_data(self._raw)
        self._refresh_cells()

    # ── side panel: settings ──────────────────────────────────────────────────
    def _toggle_settings(self):
        if self._panel_mode == "settings":
            self._show_placeholder()
            self.selected_key = None
            self._refresh_cells()
        else:
            self._show_settings_panel()

    def _show_settings_panel(self):
        self._clear_panel()
        self._panel_mode = "settings"
        self.selected_key = None
        self._refresh_cells()

        tk.Label(self.panel, text="Edit Habits",
                 bg=SURFACE2, fg=TEXT,
                 font=("Helvetica Neue", 13, "bold")).pack(pady=(20, 2))
        tk.Label(self.panel, text="Click Save to apply changes",
                 bg=SURFACE2, fg=TEXT_MUTED,
                 font=("Helvetica Neue", 9)).pack()
        tk.Frame(self.panel, bg=BORDER, height=1).pack(fill=tk.X, pady=(12, 8))

        self._habit_entries: list[tk.Entry] = []
        for habit in self.habits:
            e = tk.Entry(self.panel,
                         font=("Helvetica Neue", 10),
                         bg=SURFACE, fg=TEXT,
                         insertbackground=TEXT, relief=tk.FLAT,
                         bd=6, highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=ACCENT)
            e.insert(0, habit)
            e.pack(fill=tk.X, padx=14, pady=5)
            self._habit_entries.append(e)

        tk.Frame(self.panel, bg=BORDER, height=1).pack(fill=tk.X, pady=(10, 0))
        tk.Button(self.panel, text="Save Habits",
                  command=self._save_habits,
                  bg=ACCENT, fg="white",
                  activebackground="#6655dd", activeforeground="white",
                  relief=tk.FLAT, font=("Helvetica Neue", 10, "bold"),
                  cursor="hand2", pady=9, borderwidth=0,
                  ).pack(fill=tk.X, padx=14, pady=12)

    def _save_habits(self):
        new_habits = [e.get().strip() or f"Habit {i+1}"
                      for i, e in enumerate(self._habit_entries)]
        n = len(new_habits)
        for dk in self.days:
            arr = self.days[dk]
            while len(arr) < n:
                arr.append(False)
            self.days[dk] = arr[:n]
        self.habits[:] = new_habits
        save_data(self._raw)
        self._show_placeholder()
        self._draw_calendar()

    # ── calendar ──────────────────────────────────────────────────────────────
    def _draw_calendar(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.cell_map = {}

        for c in range(7):
            self.grid_frame.columnconfigure(c, weight=1, uniform="col")

        n     = len(self.habits)
        weeks = calendar.monthcalendar(self.year, self.month)

        for r, week in enumerate(weeks):
            self.grid_frame.rowconfigure(r, weight=1, uniform="row")
            for c, day in enumerate(week):
                if day == 0:
                    tk.Frame(self.grid_frame, bg=BG).grid(
                        row=r, column=c, sticky="nsew", padx=3, pady=3)
                    continue

                dk        = f"{self.year}-{self.month:02d}-{day:02d}"
                cell_date = date(self.year, self.month, day)
                is_future = cell_date > self.today
                completed = sum(self.days.get(dk, [])[:n])

                cell = DayCell(
                    self.grid_frame, day, dk,
                    is_today=cell_date == self.today,
                    is_future=is_future,
                    completed=completed,
                    n_habits=n,
                    on_click=self._select_day,
                )
                cell.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
                self.cell_map[dk] = cell

    def _refresh_cells(self):
        n = len(self.habits)
        for dk, cell in self.cell_map.items():
            completed = sum(self.days.get(dk, [])[:n])
            cell.refresh(completed, dk == self.selected_key)

    # ── navigation ────────────────────────────────────────────────────────────
    def _prev_month(self):
        if self.month == 1:
            self.month, self.year = 12, self.year - 1
        else:
            self.month -= 1
        self._after_nav()

    def _next_month(self):
        if self.month == 12:
            self.month, self.year = 1, self.year + 1
        else:
            self.month += 1
        self._after_nav()

    def _after_nav(self):
        self.selected_key = None
        self._show_placeholder()
        self._update_month_lbl()
        self._draw_calendar()

    def _select_day(self, date_key: str, day: int):
        self._show_day_panel(date_key, day)
        self._refresh_cells()


if __name__ == "__main__":
    app = HabitTracker()
    app.mainloop()
