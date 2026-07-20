"""
home_preview.py — the detail pane on the home screen.

Selecting one project shows what is actually inside it, laid out like an
inventory: every node type it uses as a tile, with a count in the corner
showing how many times that node appears. Under that is a free-text
description you can edit, so a project can say what it is for rather than
relying on the filename.

Nothing is selected, or several things are, means there is nothing single to
describe — the pane goes back to empty rather than showing stale detail.
"""
import os

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QTextEdit, QSizePolicy,
)


class NodeTile(QWidget):
    """One node type in the inventory: its icon, name, and how many are used."""

    def __init__(self, type_id, title, count, pixmap=None, servo=False):
        super().__init__()
        self.type_id = type_id
        self.title = title
        self.count = count
        self.pixmap = pixmap
        self.servo = servo
        self.setFixedSize(58, 58)
        self.setToolTip(f"{title} \u00d7 {count}")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)

        edge = QColor("#ff6b6b") if self.servo else QColor(255, 255, 255, 55)
        p.setPen(edge)
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawRoundedRect(r, 5, 5)

        if self.pixmap is not None and not self.pixmap.isNull():
            pm = self.pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(r.center().x() - pm.width() // 2,
                         r.top() + 6, pm)
        else:
            # no icon for this node type: show a short bit of its name instead
            p.setPen(QColor(210, 210, 210))
            f = QFont("monospace"); f.setPointSize(7); p.setFont(f)
            short = self.title.split()[0][:6]
            p.drawText(r.adjusted(0, 4, 0, -18),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                       short)

        # the name along the bottom
        p.setPen(QColor(170, 170, 170))
        f2 = QFont("monospace"); f2.setPointSize(6); p.setFont(f2)
        name = self.title if len(self.title) <= 10 else self.title[:9] + "\u2026"
        p.drawText(r.adjusted(2, 0, -2, -3),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                   name)

        # the count badge, bottom-right, only when there is more than one
        if self.count > 1:
            f3 = QFont("monospace"); f3.setPointSize(7); f3.setBold(True)
            p.setFont(f3)
            txt = str(self.count)
            bw = 13 + (len(txt) - 1) * 5
            bx = r.right() - bw - 1
            by = r.bottom() - 13
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 190))
            p.drawRoundedRect(bx, by, bw, 12, 3, 3)
            p.setPen(QColor("#ff6b6b") if self.servo else QColor("#7ecfff"))
            p.drawText(bx, by, bw, 12, Qt.AlignmentFlag.AlignCenter, txt)


class PreviewPane(QWidget):
    """The project detail pane: node inventory on top, description below."""

    def __init__(self, accent="#7ecfff"):
        super().__init__()
        self.accent = accent
        self.project = None
        self._meta = {}        # type_id -> {title, icon path}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.title = QLabel("nothing selected")
        self.title.setStyleSheet(
            "color:#eee;font-family:monospace;font-size:13px;font-weight:bold;")
        lay.addWidget(self.title)

        self.info = QLabel("")
        self.info.setStyleSheet("color:#888;font-family:monospace;font-size:10px;")
        lay.addWidget(self.info)

        # ---- the inventory grid
        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid.setMovement(QListWidget.Movement.Static)
        self.grid.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.grid.setSpacing(4)
        self.grid.setStyleSheet(
            "QListWidget{background:rgba(0,0,0,0.18);"
            "border:1px solid rgba(255,255,255,0.10);border-radius:6px;}")
        lay.addWidget(self.grid, 1)

        # ---- description, with its edit button bottom-right
        self.desc_label = QLabel("DESCRIPTION")
        self.desc_label.setStyleSheet(
            "color:#777;font-family:monospace;font-size:9px;")
        lay.addWidget(self.desc_label)

        self.desc = QTextEdit()
        self.desc.setReadOnly(True)
        self.desc.setFixedHeight(76)
        self.desc.setStyleSheet(
            "QTextEdit{background:rgba(0,0,0,0.18);color:#bbb;"
            "font-family:monospace;font-size:10px;"
            "border:1px solid rgba(255,255,255,0.10);border-radius:6px;padding:4px;}")
        lay.addWidget(self.desc)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addStretch()
        self.edit_btn = QPushButton("edit")
        self.edit_btn.setFixedSize(52, 20)
        self.edit_btn.clicked.connect(self._toggle_edit)
        btn_row.addWidget(self.edit_btn)
        lay.addLayout(btn_row)

        self._editing = False
        self._style_edit_button()
        self.show_project(None)

    # ---- appearance --------------------------------------------------------
    def set_accent(self, accent):
        self.accent = accent
        self._style_edit_button()

    def _style_edit_button(self):
        self.edit_btn.setStyleSheet(
            f"QPushButton{{background:rgba(0,0,0,0.35);color:{self.accent};"
            f"border:1px solid {self.accent};border-radius:4px;"
            f"font-family:monospace;font-size:10px;}}"
            f"QPushButton:hover{{background:rgba(255,255,255,0.15);}}")

    # ---- node metadata -----------------------------------------------------
    def set_node_meta(self, meta):
        """Give the pane the node list from the API so tiles can show the same
        titles and icons the palette uses."""
        self._meta = meta or {}
        if self.project:
            self.show_project(self.project)

    def _icon_for(self, type_id):
        try:
            from canvas import resolve_icon_path
            path = resolve_icon_path(type_id)
            if path and os.path.isfile(path):
                return QPixmap(path)
        except Exception:
            pass
        return None

    # ---- content -----------------------------------------------------------
    def show_project(self, name):
        """Show one project, or clear the pane when name is None.

        Called with None for both 'nothing selected' and 'several selected',
        since neither has a single project to describe.
        """
        self.project = name
        self._set_editing(False)
        self.grid.clear()

        if not name:
            self.title.setText("nothing selected")
            self.info.setText("select a single project to see what's in it")
            self.desc.setPlainText("")
            self.desc.setVisible(False)
            self.desc_label.setVisible(False)
            self.edit_btn.setVisible(False)
            return

        self.desc.setVisible(True)
        self.desc_label.setVisible(True)
        self.edit_btn.setVisible(True)

        try:
            from storage import load_project
            wf = load_project(name) or {}
        except Exception:
            wf = {}

        self.title.setText(name)
        nodes = wf.get("nodes") or []
        servo = (wf.get("kind") == "servo")

        # count how many of each node type this project uses
        counts = {}
        for n in nodes:
            t = n.get("type")
            if t:
                counts[t] = counts.get(t, 0) + 1

        kind = "servo / arduino" if servo else "workflow"
        bits = [f"{len(nodes)} node{'s' if len(nodes) != 1 else ''}",
                f"{len(counts)} type{'s' if len(counts) != 1 else ''}", kind]
        try:
            from storage import PROJECTS_DIR
            from datetime import datetime
            fp = os.path.join(PROJECTS_DIR, f"{name}.json")
            if os.path.isfile(fp):
                ts = datetime.fromtimestamp(os.path.getmtime(fp))
                bits.append(ts.strftime("%d %b %H:%M"))
        except Exception:
            pass
        self.info.setText("   ".join(bits))

        # build the inventory, most-used first
        for type_id, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            meta = self._meta.get(type_id) or {}
            title = meta.get("title") or type_id.split(".")[-1].replace("_", " ").title()
            tile = NodeTile(type_id, title, count, self._icon_for(type_id),
                            servo=type_id.startswith("device."))
            item = QListWidgetItem()
            item.setSizeHint(QSize(62, 62))
            self.grid.addItem(item)
            self.grid.setItemWidget(item, tile)

        if not counts:
            item = QListWidgetItem("empty project — no nodes yet")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.grid.addItem(item)

        self.desc.setPlainText(wf.get("description", ""))

    # ---- description editing ----------------------------------------------
    def _toggle_edit(self):
        if self._editing:
            self._save_description()
            self._set_editing(False)
        else:
            self._set_editing(True)

    def _set_editing(self, editing):
        self._editing = editing
        self.desc.setReadOnly(not editing)
        self.edit_btn.setText("save" if editing else "edit")
        if editing:
            self.desc.setStyleSheet(
                "QTextEdit{background:rgba(0,0,0,0.35);color:#eee;"
                "font-family:monospace;font-size:10px;"
                f"border:1px solid {self.accent};border-radius:6px;padding:4px;}}")
            self.desc.setFocus()
        else:
            self.desc.setStyleSheet(
                "QTextEdit{background:rgba(0,0,0,0.18);color:#bbb;"
                "font-family:monospace;font-size:10px;"
                "border:1px solid rgba(255,255,255,0.10);border-radius:6px;padding:4px;}")

    def _save_description(self):
        if not self.project:
            return
        try:
            from storage import load_project, save_project
            wf = load_project(self.project) or {}
            wf["description"] = self.desc.toPlainText().strip()
            save_project(self.project, wf)
        except Exception as e:
            print(f"  [preview] could not save description: {e}")
