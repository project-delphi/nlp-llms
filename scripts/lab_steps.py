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
# `## Stretch (optional) · BM25`, the bare `## Stretch (optional)`, and Lab 13's `#`.
STRETCH = re.compile(r"^#+\s+Stretch\s*\(optional\)(?:\s*·\s*(.+?))?\s*$")

# `### Stretch A · A verification node`: one of several challenges under the stretch.
SUBSTRETCH = re.compile(r"^###\s+Stretch\s+([A-Z])\s+·\s+(.+?)\s*$")


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

    Each row is {kind: part|task|challenge|challenge-item, label, title, minutes}.
    `minutes` is None when the heading does not state one.
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
        elif found := SUBSTRETCH.match(line):
            out.append(
                {
                    "kind": "challenge-item",
                    "label": f"Stretch {found[1]}",
                    "title": found[2],
                    "minutes": None,
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


def _has_tasks(found: list[dict], i: int) -> bool:
    """Whether the part at `i` has any task of its own before the next part."""
    for r in found[i + 1 :]:
        if r["kind"] == "part":
            return False
        if r["kind"] == "task":
            return True
    return False


def table(found: list[dict], briefing: dict[str, str] | None = None) -> str:
    """The core path as a table: a part is a bold row spanning its tasks. With `briefing`
    ({"Exercise 1": "2", ...}) a middle column names the briefing sections each task uses.
    The challenge is not in it; challenge() states it on its own."""
    if briefing is None:
        lines = ["| Task | Time |", "|---|---|"]
    else:
        lines = ["| Task | Briefing section | Time |", "|---|---|---|"]
    for i, r in enumerate(found):
        if r["kind"].startswith("challenge"):
            continue
        if r["kind"] == "part" and not _has_tasks(found, i):
            continue
        middle = "" if briefing is None else f" {briefing.get(r['label'], '—')} |"
        if r["kind"] == "task":
            time = f"{r['minutes']} min" if r["minutes"] else "—"
            lines.append(f"| {r['label']} · {r['title']} |{middle} {time} |")
        else:
            title = f" · {r['title']}" if r["title"] else ""
            blank = "" if briefing is None else " |"
            lines.append(f"| **{r['label']}{title}** |{blank} |")
    return "\n".join(lines)


def challenge(found: list[dict]) -> str | None:
    """The lab's optional challenge, and the pieces it breaks into when it has them.
    None when the notebook has no stretch section."""
    head = next((r for r in found if r["kind"] == "challenge"), None)
    if head is None:
        return None
    title = f" \u00b7 {head['title']}" if head["title"] else ""
    lines = [
        "::: {.challenge}",
        f"### Challenge{title} {{#challenge}}",
        "",
        "Optional, for anyone who finishes the core path early: the notebook's stretch"
        " section, after the last checkpoint.",
    ]
    items = [r for r in found if r["kind"] == "challenge-item"]
    if items:
        lines += [""] + [f"- **{r['label']}** \u00b7 {r['title']}" for r in items]
    lines.append(":::")
    return "\n".join(lines)
