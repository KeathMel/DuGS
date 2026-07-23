"""
Notes — A scratchpad node for leaving documentation, notes, images, or links inside a workflow.

SETTINGS
========
text      : main notes content (large multiline text box).
image_url : optional link to an image or diagram to associate with this note.
"""
from node_base import Node


class NotesNode(Node):
    TYPE = "notes.scratchpad"
    TITLE = "Notes"
    CATEGORY = "notes"
    ICON = "note"
    INPUTS = 1
    OUTPUTS = 1
    PARAMS = [
        {
            "key": "text",
            "label": "Notes / Documentation",
            "type": "multiline",
            "rows": 12,
            "default": "",
            "placeholder": "Write down notes, instructions, or references..."
        },
        {
            "key": "image_url",
            "label": "Image URL (optional)",
            "type": "text",
            "default": "",
            "placeholder": "https://example.com/diagram.png"
        }
    ]

    def get_tooltip(self):
        """Returns the notes preview text for UI hover tooltips."""
        notes_text = (self.params.get("text") or "").strip()
        img = (self.params.get("image_url") or "").strip()

        if not notes_text and not img:
            return "Empty note"

        preview = notes_text[:250] + ("..." if len(notes_text) > 250 else "")
        if img:
            preview += f"\n[Image: {img}]"

        return preview

    def run(self, items):
        raw_text = self.params.get("text", "") or ""
        raw_img = (self.params.get("image_url") or "").strip()

        if not items:
            resolved_text = self.rexpr(raw_text, {}) if "{{" in raw_text else raw_text
            resolved_img = self.rexpr(raw_img, {}) if "{{" in raw_img else raw_img
            return [{"json": {"notes": resolved_text, "image_url": resolved_img}}]

        out = []
        for it in items:
            j = dict(it.get("json", {}))

            notes_val = self.rexpr(raw_text, j) if "{{" in raw_text else raw_text
            img_val = self.rexpr(raw_img, j) if "{{" in raw_img else raw_img

            j["notes"] = notes_val
            j["image_url"] = img_val
            out.append({"json": j})

        return out
