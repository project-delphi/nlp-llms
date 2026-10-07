"""The task list of one lab, read from its notebook's own headings.

A lab's shape is already in its notebook: `# Part X · title` groups the work, each
`## Exercise N · title (M minutes)` (or `## Step N · ...`) is one task, and a single
`## Stretch (optional) · title` is the challenge for anyone who finishes early.
scripts/gen_tables.py turns what this module finds into `_includes/lab-NN.md`, so the
module page lists what a participant actually does without anyone restating it by hand.

Nothing here invents content: a task appears on the page only if the notebook has a
heading for it, and a time only if that heading states one.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"

# `# Part A · Tools and the graph's control flow`
PART = re.compile(r"^#+\s+Part\s+(\S+)\s+·\s+(.+?)\s*$")
# `## Exercise 3 · The chat template (6 minutes)`; `## Step 0 · ... (3 minutes)`
TASK = re.compile(r"^#+\s+(Exercise|Step)\s+(\d+)\s+·\s+(.+?)(?:\s*\((\d+)\s*minutes?\))?\s*$")
# `## Stretch (optional) · BM25`, and the bare `## Stretch (optional)`
STRETCH = re.compile(r"^##\s+Stretch\s*\(optional\)(?:\s*·\s*(.+?))?\s*$")


def headings(slug: str) -> list[str]:
    """Every markdown heading of the notebook, in document order."""
    path = NOTEBOOKS / f"{slug}.ipynb"
    if not path.exists():
        return []
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    return [
        line
        for cell in cells
        if cell["cell_type"] == "markdown"
        for line in "".join(cell["source"]).splitlines()
        if line.startswith("#")
    ]


def rows(slug: str) -> list[dict]:
    """The lab's parts, tasks and challenge, in the notebook's order.

    Each row is {kind: part|task|challenge, label, title, minutes}. `minutes` is None
    when the heading does not state one.
    """
    out: list[dict] = []
    for line in headings(slug):
        if found := PART.match(line):
            out.append(
                {
                    "kind": "part",
                    "label": f"Part {found[1]}",
                    "title": found[2],
                    "minutes": None,
                }
            )
        elif found := TASK.match(line):
            out.append(
                {
                    "kind": "task",
                    "label": f"{found[1]} {found[2]}",
                    "title": found[3],
                    "minutes": int(found[4]) if found[4] else None,
                }
            )
        elif found := STRETCH.match(line):
            # Only the first: Lab 14's `### Stretch A ...` are parts of this one.
            if not any(r["kind"] == "challenge" for r in out):
                out.append(
                    {
                        "kind": "challenge",
                        "label": "Challenge (optional)",
                        "title": found[1] or "",
                        "minutes": None,
                    }
                )
    return out


def totals(found: list[dict]) -> tuple[int, int, int]:
    """(tasks, parts, minutes stated by the task headings)."""
    tasks = [r for r in found if r["kind"] == "task"]
    return (
        len(tasks),
        len([r for r in found if r["kind"] == "part"]),
        sum(r["minutes"] or 0 for r in tasks),
    )


def table(found: list[dict]) -> str:
    """The task list as a two-column table: a part is a bold row spanning its tasks."""
    lines = ["| Task | Time |", "|---|---|"]
    for r in found:
        if r["kind"] == "task":
            time = f"{r['minutes']} min" if r["minutes"] else "—"
            lines.append(f"| {r['label']} · {r['title']} | {time} |")
        else:
            title = f" · {r['title']}" if r["title"] else ""
            lines.append(f"| **{r['label']}{title}** | |")
    return "\n".join(lines)
