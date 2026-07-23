"""
Notes node — stores plain notes or documentation text inside a workflow.

SETTINGS
========
text : the notes content ({{ }} allowed)
"""
from node_base import Node


class NotesNode(Node):
    TYPE = "notes.scratchpad"
    TITLE = "Notes"
    CATEGORY = "notes"
    INPUTS = 1
    OUTPUTS = 1
    PARAMS = [
        {"key": "text", "label": "Notes", "type": "multiline", "default": ""},
    ]

    def run(self, items):
        tpl = self.params.get("text", "") or ""
        out = []
        for it in items:
            j = dict(it.get("json", {}))
            text = self.rexpr(tpl, j) if "{{" in tpl else tpl
            j["notes"] = text
            out.append({"json": j})
        return out
