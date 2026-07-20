"""
home_preview.py — the preview pane on the home screen.

Selecting a project draws a small picture of its node graph, so you can tell
projects apart at a glance instead of by filename alone. It reads the saved
workflow JSON directly and draws a simplified version: nodes as rounded blocks,
connections as lines, coloured red for servo projects and blue for normal ones.

Under the picture is a short summary — how many nodes, what kind of project,
when it was last saved.
"""
import os
import json
from datetime import datetime

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class CanvasPreview(QWidget):
    """Draws a miniature of a workflow's node graph."""

    def __init__(self, accent="#7ecfff"):
        super().__init__()
        self.accent = accent
        self.workflow = None
        self.setMinimumHeight(150)

    def set_workflow(self, wf):
        self.workflow = wf
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(0, 0, -1, -1)

        # the frame is always drawn, so the pane reads as a defined area even
        # with nothing selected
        p.setPen(QPen(QColor(255, 255, 255, 28), 1))
        p.setBrush(QBrush(QColor(0, 0, 0, 40)))
        p.drawRoundedRect(QRectF(r), 6, 6)

        wf = self.workflow
        nodes = (wf or {}).get("nodes") or []
        if not nodes:
            p.setPen(QColor(255, 255, 255, 70))
            f = QFont("monospace"); f.setPointSize(9); p.setFont(f)
            msg = "no preview" if wf is None else "empty workflow"
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, msg)
            return

        servo = (wf.get("kind") == "servo")
        node_col = QColor("#ff6b6b") if servo else QColor(self.accent)

        # work out the graph's bounds so it can be scaled to fit the pane
        xs = [float(n.get("x", 0)) for n in nodes]
        ys = [float(n.get("y", 0)) for n in nodes]
        minx, maxx = min(xs), max(xs) + 90
        miny, maxy = min(ys), max(ys) + 60
        gw = max(1.0, maxx - minx)
        gh = max(1.0, maxy - miny)

        pad = 12
        avail_w = r.width() - pad * 2
        avail_h = r.height() - pad * 2
        scale = min(avail_w / gw, avail_h / gh, 0.5)
        # centre whatever is left over
        ox = r.left() + pad + (avail_w - gw * scale) / 2
        oy = r.top() + pad + (avail_h - gh * scale) / 2

        def pos(n):
            return QPointF(ox + (float(n.get("x", 0)) - minx) * scale,
                           oy + (float(n.get("y", 0)) - miny) * scale)

        by_name = {n.get("name"): n for n in nodes}

        # wires first, so the blocks sit on top
        p.setPen(QPen(QColor(255, 255, 255, 55), 1))
        for src, links in ((wf.get("connections") or {}).items()):
            a = by_name.get(src)
            if a is None:
                continue
            for link in links or []:
                b = by_name.get(link.get("to"))
                if b is None:
                    continue
                pa = pos(a); pb = pos(b)
                bw = 90 * scale; bh = 60 * scale
                p.drawLine(QPointF(pa.x() + bw, pa.y() + bh / 2),
                           QPointF(pb.x(), pb.y() + bh / 2))

        # the nodes
        for n in nodes:
            q = pos(n)
            bw = max(4.0, 90 * scale)
            bh = max(3.0, 60 * scale)
            p.setPen(QPen(node_col, 1))
            p.setBrush(QBrush(QColor(0, 0, 0, 120)))
            p.drawRoundedRect(QRectF(q.x(), q.y(), bw, bh),
                              min(3.0, bw / 4), min(3.0, bh / 4))


class PreviewPane(QWidget):
    """The preview picture plus a short summary underneath."""

    def __init__(self, accent="#7ecfff"):
        super().__init__()
        self.accent = accent
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self.title = QLabel("select a project")
        self.title.setStyleSheet(
            "color:#eee;font-family:monospace;font-size:13px;font-weight:bold;")
        lay.addWidget(self.title)

        self.canvas = CanvasPreview(accent)
        lay.addWidget(self.canvas, 1)

        self.info = QLabel("")
        self.info.setStyleSheet("color:#888;font-family:monospace;font-size:10px;")
        self.info.setWordWrap(True)
        lay.addWidget(self.info)

    def set_accent(self, accent):
        self.accent = accent
        self.canvas.accent = accent
        self.canvas.update()

    def show_project(self, name, path=None):
        """Load a project by name and draw it."""
        if not name:
            self.title.setText("select a project")
            self.info.setText("")
            self.canvas.set_workflow(None)
            return
        wf = None
        try:
            from storage import load_project
            wf = load_project(name)
        except Exception:
            wf = None
        self.title.setText(name)
        self.canvas.set_workflow(wf)

        if not wf:
            self.info.setText("could not read this project")
            return
        nodes = wf.get("nodes") or []
        kind = "servo / arduino" if wf.get("kind") == "servo" else "workflow"
        bits = [f"{len(nodes)} node{'s' if len(nodes) != 1 else ''}", kind]
        try:
            from storage import PROJECTS_DIR
            fp = os.path.join(PROJECTS_DIR, f"{name}.json")
            if os.path.isfile(fp):
                ts = datetime.fromtimestamp(os.path.getmtime(fp))
                bits.append(f"saved {ts.strftime('%d %b %H:%M')}")
        except Exception:
            pass
        self.info.setText("   ".join(bits))
