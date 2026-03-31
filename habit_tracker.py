#!/usr/bin/env python3
"""Habit Tracker — PyQt5 modern dark UI."""

import sys, json, os, calendar
from datetime import datetime, date

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QGridLayout, QFrame, QLineEdit,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QBrush, QPen, QFont

# ── persistence ───────────────────────────────────────────────────────────────
DATA_FILE      = os.path.expanduser("~/.habit_tracker_data.json")
DEFAULT_HABITS = [
    "Exercise", "Read for 30 minutes", "Meditate",
    "Drink 8 glasses of water", "Sleep 8 hours",
]

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            raw = json.load(f)
        # migrate old format (dict-of-dicts keyed by habit name)
        if raw and "habits" not in raw:
            habits = list(DEFAULT_HABITS)
            days   = {dk: [bool(dv.get(h, False)) for h in habits]
                      for dk, dv in raw.items() if isinstance(dv, dict)}
            return {"habits": habits, "days": days}
        return raw
    return {"habits": list(DEFAULT_HABITS), "days": {}}

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── palette ───────────────────────────────────────────────────────────────────
BG       = "#0d0d1a"
SURFACE  = "#13131f"
SURFACE2 = "#1a1a2e"
BORDER   = "#252538"
TEXT     = "#e2e2f0"
MUTED    = "#5a5a7a"
ACCENT   = "#7c6af7"
RED      = "#d95f5f"
ORANGE   = "#d4874a"
GREEN    = "#3db870"
NEUTRAL  = "#252538"
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def _cell_color(completed: int, n: int, is_future: bool) -> str:
    if is_future:      return NEUTRAL
    if completed == 0: return RED
    if completed == n: return GREEN
    return ORANGE

# ── calendar day cell ─────────────────────────────────────────────────────────
class DayCell(QWidget):
    clicked = pyqtSignal(str, int)  # date_key, day

    def __init__(self, day: int, date_key: str, is_today: bool,
                 is_future: bool, completed: int, n_habits: int):
        super().__init__()
        self.day       = day
        self.date_key  = date_key
        self.is_today  = is_today
        self.is_future = is_future
        self.completed = completed
        self.n_habits  = n_habits
        self.selected  = False
        self._hovered  = False
        self.setMinimumSize(56, 52)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if not is_future:
            self.setCursor(Qt.PointingHandCursor)
            self.setMouseTracking(True)

    def refresh(self, completed: int, selected: bool):
        self.completed = completed
        self.selected  = selected
        self.update()

    def mousePressEvent(self, e):
        if not self.is_future and e.button() == Qt.LeftButton:
            self.clicked.emit(self.date_key, self.day)

    def enterEvent(self, e):
        if not self.is_future:
            self._hovered = True
            self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h, r = self.width(), self.height(), 10

        fill = QColor(_cell_color(self.completed, self.n_habits, self.is_future))
        if self._hovered:
            fill = fill.darker(120)

        if self.is_today or self.selected:
            outer = QPainterPath()
            outer.addRoundedRect(QRectF(0, 0, w, h), r, r)
            p.fillPath(outer, QBrush(QColor(ACCENT)))
            inner = QPainterPath()
            inner.addRoundedRect(QRectF(3, 3, w - 6, h - 6), r - 2, r - 2)
            p.fillPath(inner, QBrush(fill))
        else:
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, w, h), r, r)
            p.fillPath(path, QBrush(fill))

        # Day number
        f = QFont("Helvetica Neue", 11)
        f.setBold(self.is_today)
        p.setFont(f)
        p.setPen(QColor(TEXT))
        p.drawText(QRectF(8, 5, w - 16, 22),
                   Qt.AlignLeft | Qt.AlignVCenter, str(self.day))

        # Progress dots
        if not self.is_future and self.n_habits > 0:
            dr, gap = 5, 4
            total_w = self.n_habits * dr + (self.n_habits - 1) * gap
            x0 = max(6, (w - total_w) // 2)
            y0 = h - 13
            p.setPen(Qt.NoPen)
            for i in range(self.n_habits):
                x = x0 + i * (dr + gap)
                dot = QColor(TEXT) if i < self.completed else fill.darker(200)
                p.setBrush(QBrush(dot))
                p.drawEllipse(x, y0, dr, dr)

        p.end()

# ── circular checkbox ─────────────────────────────────────────────────────────
class CircleCheck(QWidget):
    clicked = pyqtSignal()

    def __init__(self, checked: bool):
        super().__init__()
        self.checked = checked
        self.setFixedSize(20, 20)
        self.setCursor(Qt.PointingHandCursor)

    def set_checked(self, v: bool):
        self.checked = v
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.checked:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(ACCENT)))
            p.drawEllipse(1, 1, 18, 18)
            p.setPen(QPen(QColor("white"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(5, 10, 8, 14)
            p.drawLine(8, 14, 15, 6)
        else:
            p.setPen(QPen(QColor(BORDER), 2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(1, 1, 18, 18)
        p.end()

# ── habit row ─────────────────────────────────────────────────────────────────
class HabitRow(QFrame):
    toggled = pyqtSignal()

    def __init__(self, text: str, checked: bool):
        super().__init__()
        self.checked = checked
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"background: {SURFACE2};")
        self.setCursor(Qt.PointingHandCursor)

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 10, 12, 10)
        row.setSpacing(12)

        self._check = CircleCheck(checked)
        self._check.clicked.connect(self._do_toggle)
        row.addWidget(self._check)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {TEXT}; font-size: 10pt; background: transparent;")
        lbl.mousePressEvent = lambda e: self._do_toggle()
        row.addWidget(lbl, 1)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._do_toggle()

    def _do_toggle(self):
        self.checked = not self.checked
        self._check.set_checked(self.checked)
        self.toggled.emit()

# ── divider helper ────────────────────────────────────────────────────────────
def _divider(color=BORDER, indent=0) -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {color}; margin: 0 {indent}px;")
    return line

# ── main window ───────────────────────────────────────────────────────────────
class HabitTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Habit Tracker")
        self.setMinimumSize(860, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        self._raw   = load_data()
        self.habits = self._raw.setdefault("habits", list(DEFAULT_HABITS))
        self.days   = self._raw.setdefault("days",   {})
        now         = datetime.now()
        self.year, self.month = now.year, now.month
        self.today  = date.today()
        self.sel_key: str | None = None
        self._panel_mode = "placeholder"
        self.cell_map: dict[str, DayCell] = {}
        self._habit_rows: list[HabitRow]  = []

        # Root layout
        root = QWidget()
        root.setStyleSheet(f"background: {BG};")
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._make_header())

        body = QHBoxLayout()
        body.setContentsMargins(16, 8, 16, 16)
        body.setSpacing(10)

        # Calendar (left)
        cal = QWidget()
        cal.setStyleSheet(f"background: {BG};")
        cal_v = QVBoxLayout(cal)
        cal_v.setContentsMargins(0, 0, 0, 0)
        cal_v.setSpacing(0)
        cal_v.addWidget(self._make_day_labels())
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet(f"background: {BG};")
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(4)
        self.grid.setContentsMargins(0, 4, 0, 0)
        cal_v.addWidget(self.grid_widget, 1)
        body.addWidget(cal, 1)

        # Side panel (right, fixed width)
        self.panel = QFrame()
        self.panel.setFixedWidth(252)
        self.panel.setFrameShape(QFrame.NoFrame)
        self.panel.setStyleSheet(
            f"QFrame {{ background: {SURFACE2}; border-radius: 10px; }}")
        self.panel_v = QVBoxLayout(self.panel)
        self.panel_v.setContentsMargins(0, 0, 0, 0)
        self.panel_v.setSpacing(0)
        body.addWidget(self.panel)

        vbox.addLayout(body, 1)

        self._show_placeholder()
        self._draw_calendar()

    # ── header ────────────────────────────────────────────────────────────────
    def _make_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setStyleSheet(f"background: {SURFACE};")
        v = QVBoxLayout(hdr)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        bar = QWidget()
        bar.setFixedHeight(2)
        bar.setStyleSheet(f"background: {ACCENT};")
        v.addWidget(bar)

        inner = QWidget()
        inner.setStyleSheet(f"background: {SURFACE};")
        h = QHBoxLayout(inner)
        h.setContentsMargins(16, 6, 16, 6)
        h.setSpacing(4)

        nb = f"""QPushButton {{
                    background: transparent; color: {MUTED};
                    border: none; font-size: 16pt; padding: 2px 10px; }}
                 QPushButton:hover {{
                    color: {TEXT}; background: {SURFACE2};
                    border-radius: 6px; }}"""
        prev = QPushButton("‹")
        prev.setStyleSheet(nb)
        prev.setCursor(Qt.PointingHandCursor)
        prev.clicked.connect(self._prev_month)
        h.addWidget(prev)

        nxt = QPushButton("›")
        nxt.setStyleSheet(nb)
        nxt.setCursor(Qt.PointingHandCursor)
        nxt.clicked.connect(self._next_month)
        h.addWidget(nxt)

        self.month_lbl = QLabel()
        self.month_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 14pt; font-weight: bold;"
            f" padding-left: 8px; background: transparent;")
        self._update_month_lbl()
        h.addWidget(self.month_lbl)
        h.addStretch()

        gear = QPushButton("⚙")
        gear.setStyleSheet(nb)
        gear.setCursor(Qt.PointingHandCursor)
        gear.clicked.connect(self._toggle_settings)
        h.addWidget(gear)

        v.addWidget(inner)
        return hdr

    def _make_day_labels(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        for name in DAY_NAMES:
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color: {MUTED}; font-size: 9pt; font-weight: bold;"
                f" background: transparent;")
            h.addWidget(lbl, 1)
        return w

    def _update_month_lbl(self):
        self.month_lbl.setText(
            datetime(self.year, self.month, 1).strftime("%B %Y"))

    # ── side panel ────────────────────────────────────────────────────────────
    def _clear_panel(self):
        while self.panel_v.count():
            item = self.panel_v.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._habit_rows = []

    def _show_placeholder(self):
        self._clear_panel()
        self._panel_mode = "placeholder"
        lbl = QLabel("Select a day\nto track habits")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color: {MUTED}; font-size: 11pt; background: transparent;")
        self.panel_v.addStretch()
        self.panel_v.addWidget(lbl)
        self.panel_v.addStretch()

    def _show_day_panel(self, date_key: str, day: int):
        self._clear_panel()
        self._panel_mode = "day"
        self.sel_key = date_key

        dt     = datetime(self.year, self.month, day)
        checks = list(self.days.get(date_key, []))
        while len(checks) < len(self.habits):
            checks.append(False)

        # Date heading
        head = QWidget()
        head.setStyleSheet(f"background: {SURFACE2};")
        hv = QVBoxLayout(head)
        hv.setContentsMargins(0, 20, 0, 14)
        hv.setSpacing(3)
        dow = QLabel(dt.strftime("%A"))
        dow.setAlignment(Qt.AlignCenter)
        dow.setStyleSheet(
            f"color: {MUTED}; font-size: 10pt; background: transparent;")
        hv.addWidget(dow)
        dlbl = QLabel(dt.strftime("%-d %B %Y"))
        dlbl.setAlignment(Qt.AlignCenter)
        dlbl.setStyleSheet(
            f"color: {TEXT}; font-size: 13pt; font-weight: bold;"
            f" background: transparent;")
        hv.addWidget(dlbl)
        self.panel_v.addWidget(head)
        self.panel_v.addWidget(_divider())

        for i, (habit, checked) in enumerate(zip(self.habits, checks)):
            row = HabitRow(habit, bool(checked))
            row.toggled.connect(self._on_toggle)
            self.panel_v.addWidget(row)
            self._habit_rows.append(row)
            if i < len(self.habits) - 1:
                self.panel_v.addWidget(_divider(indent=16))

        self.panel_v.addStretch()

    def _on_toggle(self):
        if not self.sel_key:
            return
        self.days[self.sel_key] = [r.checked for r in self._habit_rows]
        save_data(self._raw)
        self._refresh_cells()

    # ── settings panel ────────────────────────────────────────────────────────
    def _toggle_settings(self):
        if self._panel_mode == "settings":
            self._show_placeholder()
            self.sel_key = None
            self._refresh_cells()
        else:
            self._show_settings()

    def _show_settings(self):
        self._clear_panel()
        self._panel_mode = "settings"
        self.sel_key = None
        self._refresh_cells()

        head = QWidget()
        head.setStyleSheet(f"background: {SURFACE2};")
        hv = QVBoxLayout(head)
        hv.setContentsMargins(16, 20, 16, 12)
        hv.setSpacing(4)
        hv.addWidget(QLabel("Edit Habits", styleSheet=
            f"color: {TEXT}; font-size: 13pt; font-weight: bold;"
            f" background: transparent;"))
        hv.addWidget(QLabel("Rename any habit then save", styleSheet=
            f"color: {MUTED}; font-size: 9pt; background: transparent;"))
        self.panel_v.addWidget(head)
        self.panel_v.addWidget(_divider())

        entry_ss = f"""QLineEdit {{
            background: {SURFACE}; color: {TEXT};
            border: 1px solid {BORDER}; border-radius: 6px;
            padding: 6px 10px; font-size: 10pt; }}
        QLineEdit:focus {{ border-color: {ACCENT}; }}"""

        form = QWidget()
        form.setStyleSheet(f"background: {SURFACE2};")
        fv = QVBoxLayout(form)
        fv.setContentsMargins(14, 10, 14, 4)
        fv.setSpacing(8)
        self._entries: list[QLineEdit] = []
        for habit in self.habits:
            e = QLineEdit(habit)
            e.setStyleSheet(entry_ss)
            fv.addWidget(e)
            self._entries.append(e)
        self.panel_v.addWidget(form)

        self.panel_v.addWidget(_divider())

        btn_wrap = QWidget()
        btn_wrap.setStyleSheet(f"background: {SURFACE2};")
        bv = QVBoxLayout(btn_wrap)
        bv.setContentsMargins(14, 10, 14, 14)
        save_btn = QPushButton("Save Habits")
        save_btn.setStyleSheet(f"""QPushButton {{
            background: {ACCENT}; color: white; border: none;
            border-radius: 6px; font-size: 10pt; font-weight: bold;
            padding: 9px; }}
        QPushButton:hover {{ background: #6655dd; }}""")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_habits)
        bv.addWidget(save_btn)
        self.panel_v.addWidget(btn_wrap)
        self.panel_v.addStretch()

    def _save_habits(self):
        new = [e.text().strip() or f"Habit {i+1}"
               for i, e in enumerate(self._entries)]
        n = len(new)
        for dk in self.days:
            arr = self.days[dk]
            while len(arr) < n:
                arr.append(False)
            self.days[dk] = arr[:n]
        self.habits[:] = new
        save_data(self._raw)
        self._show_placeholder()
        self._draw_calendar()

    # ── calendar ──────────────────────────────────────────────────────────────
    def _draw_calendar(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cell_map = {}

        n     = len(self.habits)
        weeks = calendar.monthcalendar(self.year, self.month)

        for r, week in enumerate(weeks):
            self.grid.setRowStretch(r, 1)
            for c, day in enumerate(week):
                self.grid.setColumnStretch(c, 1)
                if day == 0:
                    spacer = QWidget()
                    spacer.setStyleSheet(f"background: {BG};")
                    self.grid.addWidget(spacer, r, c)
                    continue
                dk        = f"{self.year}-{self.month:02d}-{day:02d}"
                cell_date = date(self.year, self.month, day)
                is_future = cell_date > self.today
                completed = sum(self.days.get(dk, [])[:n])
                cell = DayCell(day, dk,
                               is_today=cell_date == self.today,
                               is_future=is_future,
                               completed=completed,
                               n_habits=n)
                cell.clicked.connect(self._select_day)
                self.grid.addWidget(cell, r, c)
                self.cell_map[dk] = cell

    def _refresh_cells(self):
        n = len(self.habits)
        for dk, cell in self.cell_map.items():
            completed = sum(self.days.get(dk, [])[:n])
            cell.refresh(completed, dk == self.sel_key)

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
        self.sel_key = None
        self._show_placeholder()
        self._update_month_lbl()
        self._draw_calendar()

    def _select_day(self, date_key: str, day: int):
        self._show_day_panel(date_key, day)
        self._refresh_cells()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = HabitTracker()
    win.show()
    sys.exit(app.exec_())
