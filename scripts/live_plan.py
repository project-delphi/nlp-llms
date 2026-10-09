"""Each briefing's live teaching sequence: what is taught in the room, in what order, and
for how long, including the activities (predictions, checks, the demo) that the minutes
must hold.

The plan lives in the briefing's front matter, next to the text it times:

    live:
      - {section: 1, minutes: 5}
      - {section: 2, minutes: 7, activities: [{block: chk-sdpa, minutes: 2}]}
      - {section: 6, minutes: 4, activities: [{block: demo-scaling, minutes: 4}]}

`minutes` is the exposition time of the numbered section (`## N. Title`); each activity
names a block on the page by its id (`::: {#chk-sdpa .self-check}`, `.demo`, `.predict`
or `.discuss`) and the minutes it takes in the room. Exposition and activities together
fill the module's briefing minutes exactly (45 on Day 1, 55 on Days 2 to 5).

A numbered section left out of the plan is reference material: its heading carries
`{.reference}`, and it stays on the page, styled, for reading after class.

Beside the plan, `lab:` names the sections each exercise of the module's notebook uses:

    lab:
      - {exercise: 1, sections: [2]}
      - {exercise: 6, sections: [6]}

One entry per `Exercise N` heading of the notebook, in order. From it the agenda gets a
reading guide (read now, use in the lab, read later), and the "In the Lab" table a column
naming each exercise's sections.

scripts/gen_tables.py writes `_includes/live-NN.md` (the briefing's timing table) and
`_includes/pace-NN.md` (the pace sheet's briefing rows) from this; tests/test_live.py
checks it. filters/live.lua marks the planned blocks so the page shows which ones are
used in the room.
"""

from __future__ import annotations

import re
from pathlib import Path

import lab_steps
import yaml

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"

KINDS = {"self-check": "Check yourself", "demo": "Demo", "predict": "Predict", "discuss": "Discuss"}
SECTION = re.compile(r"^## (\d+)\. (.+?)\s*(\{[^}]*\})?\s*$")
OPEN_DIV = re.compile(r"^:::+\s*\S")
CLOSE_DIV = re.compile(r"^:::+\s*$")
FENCE = re.compile(r"^(`{3,}|~{3,})")


def read(slug: str) -> dict:
    """Front matter, numbered sections and identified activity blocks of a briefing.

    `blocks` maps each activity block's id to its kind, and `block_sections` to the
    numbered section it sits in (None outside one: before the first, or under an
    unnumbered heading such as Summary); `duplicates` lists ids used by more than one
    activity block. Only top-level headings are sections: a `##` title inside a
    callout is not, and neither is anything inside fenced code."""
    text = (MODULES / f"{slug}.qmd").read_text(encoding="utf-8")
    front = {}
    body = text
    if text.startswith("---\n"):
        end = text.index("\n---", 4)
        front = yaml.safe_load(text[4:end]) or {}
        body = text[end + 4 :]
    sections, blocks, block_sections, duplicates = {}, {}, {}, []
    current, depth, fence = None, 0, None
    for line in body.splitlines():
        if fence:
            if line.startswith(fence) and not line[len(fence) :].strip():
                fence = None
            continue
        opened = FENCE.match(line)
        if opened:
            fence = opened.group(1)
            continue
        if depth == 0 and line.startswith("## "):
            m = SECTION.match(line)
            current = int(m.group(1)) if m else None
            if m:
                sections[current] = {
                    "title": m.group(2),
                    "reference": ".reference" in (m.group(3) or ""),
                }
        if CLOSE_DIV.match(line):
            depth = max(depth - 1, 0)
        elif OPEN_DIV.match(line):
            depth += 1
            attrs = re.match(r"^:::+\s*\{([^}]*)\}", line)
            # Pandoc attributes in any order: {#chk-x .self-check} or {.self-check #chk-x}.
            words = attrs.group(1).split() if attrs else []
            ids = [w[1:] for w in words if w.startswith("#")]
            kinds = [k for k in KINDS if f".{k}" in words]
            if ids and kinds:
                if ids[0] in blocks:
                    duplicates.append(ids[0])
                blocks[ids[0]] = kinds[0]
                block_sections[ids[0]] = current
    return {
        "front": front,
        # What the page has for reading afterwards, for the reading guide.
        "later": {
            "optional": 'title="Optional' in body,
            "after-lab": 'title="After the Lab' in body,
            "further": "\n## Further Reading" in body,
        },
        "sections": sections,
        "blocks": blocks,
        "block_sections": block_sections,
        "duplicates": duplicates,
    }


def rows(slug: str, briefing: dict | None = None) -> list[dict]:
    """The plan in order, with section titles and activity kinds filled in. A plan
    whose entries are malformed raises ValueError with the readable problems."""
    briefing = briefing or read(slug)
    found = shape_problems(slug, briefing["front"].get("live") or [])
    if found:
        raise ValueError("\n".join(found))
    out = []
    for entry in briefing["front"].get("live") or []:
        n = entry["section"]
        out.append(
            {
                "n": n,
                "title": briefing["sections"].get(n, {}).get("title", "?"),
                "minutes": entry["minutes"],
                "activities": [
                    {
                        "block": a["block"],
                        "kind": briefing["blocks"].get(a["block"], "?"),
                        "minutes": a["minutes"],
                    }
                    for a in entry.get("activities", [])
                ],
            }
        )
    return out


def totals(plan: list[dict]) -> tuple[int, int]:
    """(exposition minutes, activity minutes)."""
    exposition = sum(r["minutes"] for r in plan)
    activities = sum(a["minutes"] for r in plan for a in r["activities"])
    return exposition, activities


def shape_problems(slug: str, plan) -> list[str]:
    """Entries that are not {section: int, minutes: int, activities: [{block, minutes}]}."""
    if not isinstance(plan, list):
        return [f"{slug}: `live` must be a list of sections"]
    out = []
    for i, e in enumerate(plan, 1):
        where = f"{slug}: `live` entry {i} ({e!r})"
        if not isinstance(e, dict) or set(e) - {"section", "minutes", "activities"}:
            out.append(f"{where} must have only the keys section, minutes and activities")
            continue
        if not (is_count(e.get("section")) and e["section"] > 0 and is_count(e.get("minutes"))):
            out.append(f"{where} needs a positive integer section and whole minutes (0 or more)")
        activities = e.get("activities", [])
        if not isinstance(activities, list) or not all(
            isinstance(a, dict)
            and set(a) == {"block", "minutes"}
            and isinstance(a["block"], str)
            and is_count(a["minutes"])
            and a["minutes"] > 0
            for a in activities
        ):
            out.append(f"{where}: each activity is {{block: <id>, minutes: <positive integer>}}")
    return out


def is_count(x) -> bool:
    """A whole number of 0 or more; YAML's true and false are not numbers here."""
    return type(x) is int and x >= 0


def lab_map(briefing: dict) -> dict[int, list[int]]:
    """{exercise: [sections]} from the `lab:` front matter; empty when there is none."""
    entries = briefing["front"].get("lab") or []
    return {e["exercise"]: list(e["sections"]) for e in entries if isinstance(e, dict)}


def notebook_exercises(slug: str) -> list[int]:
    """The `Exercise N` numbers of the module's notebook, in order."""
    return [
        int(r["label"].split()[1])
        for r in lab_steps.rows(slug)
        if r["kind"] == "task" and r["label"].startswith("Exercise")
    ]


def lab_problems(slug: str, briefing: dict) -> list[str]:
    """Everything wrong with a briefing's `lab:` map."""
    entries = briefing["front"].get("lab")
    exercises = notebook_exercises(slug)
    if entries is None:
        return [f"{slug}: no `lab` map in the front matter"] if exercises else []
    out = []
    if not isinstance(entries, list) or not all(
        isinstance(e, dict)
        and set(e) == {"exercise", "sections"}
        and is_count(e["exercise"])
        and isinstance(e["sections"], list)
        and e["sections"]
        and all(is_count(n) and n > 0 for n in e["sections"])
        for e in entries
    ):
        return [f"{slug}: each `lab` entry is {{exercise: <n>, sections: [<n>, ...]}}"]
    mapped = [e["exercise"] for e in entries]
    if mapped != exercises:
        out.append(f"{slug}: the `lab` map names exercises {mapped}; the notebook has {exercises}")
    for e in entries:
        for n in e["sections"]:
            if n not in briefing["sections"]:
                out.append(
                    f"{slug}: exercise {e['exercise']} names section {n}, which does not exist"
                )
    return out


def _numbers(ns: list[int]) -> str:
    """[1, 2, 3, 5] -> '1–3 and 5'."""
    runs: list[list[int]] = []
    for n in sorted(set(ns)):
        if runs and n == runs[-1][-1] + 1:
            runs[-1].append(n)
        else:
            runs.append([n])
    parts = []
    for r in runs:
        # A run of three or more is a range; a pair is two items: "6 and 7", "1, 2 and 4".
        parts += [f"{r[0]}–{r[-1]}"] if len(r) > 2 else [str(n) for n in r]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def _sections_word(ns: list[int]) -> str:
    return f"section{'s' if len(ns) > 1 else ''} {_numbers(ns)}"


def guide(slug: str, briefing: dict | None = None) -> str:
    """Read now, use in the lab, read later: the reading guide under the agenda."""
    briefing = briefing or read(slug)
    sections = briefing["sections"]
    planned = [r["n"] for r in rows(slug, briefing)]
    reference = [n for n, s in sorted(sections.items()) if s["reference"]]
    used = lab_map(briefing)
    lines = ["::: {.reading-guide}"]
    lines += [
        "**Read now** · " + _sections_word(planned).capitalize() + ", in the agenda above.",
        "",
    ]
    if used:
        groups: list[tuple[list[int], list[int]]] = []
        for ex, ns in used.items():
            if groups and groups[-1][1] == ns and groups[-1][0][-1] == ex - 1:
                groups[-1][0].append(ex)
            else:
                groups.append(([ex], ns))
        items = []
        for exs, ns in groups:
            who = f"Exercise {exs[0]}" if len(exs) == 1 else f"Exercises {_numbers(exs)}"
            refs = [n for n in ns if sections[n]["reference"]]
            note = (
                f" ({_sections_word(refs)}: **Reference**; the exercise restates what it needs)"
                if refs
                else ""
            )
            items.append(f"{who}: {_sections_word(ns)}{note}")
        lines += ["**Use in the lab** · " + "; ".join(items) + ".", ""]
    later = [f"section {n}, *{sections[n]['title']}* (**Reference**)" for n in reference]
    has = briefing.get("later", {})
    marks = [
        m
        for m, k in (("**Optional**", "optional"), ("**After the Lab**", "after-lab"))
        if has.get(k)
    ]
    if marks:
        later.append(f"the collapsed callouts marked {' or '.join(marks)}")
    if has.get("further"):
        later.append("[Further Reading](#further-reading)")
    text = "; ".join(later)
    lines += ["**Read later** · " + text[0].upper() + text[1:] + ".", ":::"]
    return "\n".join(lines)


def problems(slug: str, lecture_minutes: int) -> list[str]:
    """Everything wrong with a briefing's plan, as readable strings."""
    briefing = read(slug)
    plan = briefing["front"].get("live")
    if not plan:
        return [f"{slug}: no `live` plan in the front matter"]
    out = shape_problems(slug, plan)
    if out:
        return out
    planned = [e["section"] for e in plan]
    if len(planned) != len(set(planned)):
        out.append(f"{slug}: a section is planned twice")
    for n, section in briefing["sections"].items():
        if section["reference"] and n in planned:
            out.append(f"{slug}: section {n} is marked .reference but is in the plan")
        if not section["reference"] and n not in planned:
            out.append(f"{slug}: section {n} is neither planned nor marked .reference")
    for n in planned:
        if n not in briefing["sections"]:
            out.append(f"{slug}: the plan names section {n}, which does not exist")
    if planned != sorted(planned):
        out.append(f"{slug}: the plan is not in section order")
    used = [a["block"] for e in plan for a in e.get("activities", [])]
    for block in used:
        if block not in briefing["blocks"]:
            out.append(f"{slug}: activity block #{block} is not an identified activity block")
    for e in plan:
        for a in e.get("activities", []):
            where = briefing["block_sections"].get(a["block"], e["section"])
            if where != e["section"]:
                out.append(
                    f"{slug}: activity block #{a['block']} is planned under section"
                    f" {e['section']} but sits in section {where}"
                )
    for block in sorted(set(briefing["duplicates"])):
        out.append(f"{slug}: more than one activity block has the id #{block}")
    if len(used) != len(set(used)):
        out.append(f"{slug}: an activity block is planned twice")
    out += lab_problems(slug, briefing)
    exposition, activities = totals(rows(slug, briefing))
    if exposition + activities != lecture_minutes:
        out.append(
            f"{slug}: the plan fills {exposition + activities} minutes"
            f" ({exposition} exposition + {activities} activities), not {lecture_minutes}"
        )
    return out


def _activity(a: dict, link: bool) -> str:
    kind = KINDS.get(a["kind"], a["kind"])
    return (
        f"[{kind}](#{a['block']}) ({a['minutes']} min)" if link else f"{kind} ({a['minutes']} min)"
    )


def _timed_rows(plan: list[dict], link: bool) -> tuple[list[str], int]:
    """Table rows with minute ranges from the start of the briefing, and the end minute.
    Shared by the briefing's table (activities linked) and the pace sheet (plain)."""
    lines = []
    t = 0
    for r in plan:
        length = r["minutes"] + sum(a["minutes"] for a in r["activities"])
        activity = "; ".join(_activity(a, link) for a in r["activities"]) or "—"
        lines.append(f"| {t}–{t + length} | {r['n']}. {r['title']} | {activity} |")
        t += length
    return lines, t


def table(slug: str, briefing: dict | None = None) -> str:
    """The briefing's timing table: minute ranges, sections and activities in the room."""
    briefing = briefing or read(slug)
    plan = rows(slug, briefing)
    body, t = _timed_rows(plan, link=True)
    lines = ["| Minutes | Section | In the room |", "|---|---|---|", *body]
    exposition, activities = totals(plan)
    lines.append(
        f"| **{t}** | **Total** | **{exposition} minutes of exposition,"
        f" {activities} of activities** |"
    )
    return "\n".join(
        [
            "::: {.live-plan}",
            "\n".join(lines),
            ":::",
            "",
            "Checks, demos and predictions listed here are part of the live session and its"
            " minutes; the others on the page are for reading afterwards.",
            "",
            guide(slug, briefing),
        ]
    )


def pace_rows(slug: str, briefing: dict | None = None) -> str:
    """The pace sheet's briefing rows: minute ranges from the start of the module's slot."""
    body, _ = _timed_rows(rows(slug, briefing), link=False)
    return "\n".join(["| Minutes | Segment | In the room |", "|---|---|---|", *body])
