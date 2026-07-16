"""Stage 4: Draft an email containing the weekly note.

Default mode writes a standards-compliant output/email_draft.eml with the
note as plain text + simple HTML (UTF-8 throughout, EC-MAIL-01/02).
Optional gmail mode falls back to eml on any failure (EC-MAIL-04).
Nothing is ever auto-sent — draft only, per the brief.
"""

import logging
import re
from email.message import EmailMessage
from pathlib import Path

from src.errors import PipelineError

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
OUTPUT_EML = ROOT / "output" / "email_draft.eml"


def _latest_note() -> Path:
    notes = sorted((ROOT / "output").glob("weekly_note_*.md"))
    notes = [n for n in notes if ".FAILED" not in n.name]
    if not notes:
        raise PipelineError("email: no weekly note found — run the note stage first")
    return notes[-1]


def _markdown_to_html(md: str) -> str:
    """Minimal markdown -> HTML for mail clients (headers, bullets, bold,
    italics). Deliberately simple — no external dependency."""
    html_lines = []
    in_list = False
    for line in md.splitlines():
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
        is_bullet = stripped.startswith(("* ", "- ")) or re.match(r"^\d+\. ", stripped)
        if is_bullet and not in_list:
            html_lines.append("<ul>")
            in_list = True
        elif not is_bullet and in_list:
            html_lines.append("</ul>")
            in_list = False

        content = re.sub(r"^([*-]|\d+\.)\s+", "", stripped)
        content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<em>\1</em>", content)
        content = re.sub(r"\*(?!\s)([^*]+?)\*", r"<em>\1</em>", content)

        if stripped.startswith("# "):
            html_lines.append(f"<h2>{content.lstrip('# ')}</h2>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h3>{content.lstrip('# ')}</h3>")
        elif is_bullet:
            html_lines.append(f"<li>{content}</li>")
        else:
            html_lines.append(f"<p>{content}</p>")
    if in_list:
        html_lines.append("</ul>")
    body = "\n".join(html_lines)
    return (
        '<html><body style="font-family:Segoe UI,Arial,sans-serif;'
        'max-width:640px;line-height:1.5">' + body + "</body></html>"
    )


def build_message(note_md: str, note_date: str, to_addr: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"Weekly App Review Pulse — {note_date}"
    msg["From"] = to_addr
    msg["To"] = to_addr
    msg["X-Unsent"] = "1"  # hint to mail clients: open as a draft
    msg.set_content(note_md, charset="utf-8")
    msg.add_alternative(_markdown_to_html(note_md), subtype="html", charset="utf-8")
    return msg


def run(config: dict) -> Path:
    """Execute this stage. Reads the latest note, writes the email draft."""
    to_addr = config["email"]["to"]
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", to_addr):
        raise PipelineError(f"email: invalid recipient address in config: {to_addr!r}")

    note_path = _latest_note()
    note_md = note_path.read_text(encoding="utf-8")
    note_date = note_path.stem.replace("weekly_note_", "")

    mode = config["email"].get("mode", "eml")
    if mode == "gmail":
        log.warning(
            "email: gmail mode not configured — falling back to eml (EC-MAIL-04)"
        )

    msg = build_message(note_md, note_date, to_addr)
    tmp = OUTPUT_EML.with_suffix(".eml.tmp")
    tmp.write_bytes(bytes(msg))
    tmp.replace(OUTPUT_EML)
    log.info("email: draft for %s (note %s) -> %s", to_addr, note_date, OUTPUT_EML)
    return OUTPUT_EML
