"""The glossary and the results worksheet, from their data files.

_glossary.yml   terms and symbols -> _includes/glossary.md (glossary.qmd)
_worksheet.yml  result rows       -> _includes/worksheet.md (worksheet.qmd) and
                                     downloads/results-worksheet.csv

scripts/gen_tables.py writes the files; tests/test_learner_pages.py checks that every
module, section, exercise, dataset and cross-reference named in the data exists. Nothing
here is a result: the worksheet's result columns are blank for participants to fill.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

import lab_steps
import live_plan
import yaml

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / "_glossary.yml"
WORKSHEET = ROOT / "_worksheet.yml"
WORKSHEET_CSV = ROOT / "downloads" / "results-worksheet.csv"
# `dataset: generated`: data the notebook builds itself from a fixed seed (Lab 4's dates,
# Lab 8's announcements, Lab 9's toy task), so it has no entry under datasets:.
GENERATED = "generated"
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CSV_COLUMNS = [
    "group",
    "lab",
    "exercise",
    "model",
    "dataset",
    "split",
    "unit",
    "metric",
    "direction",
    "baseline",
    "seed",
    "result",
    "path",
    "environment",
    "seconds",
    "interpretation",
]


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def _module_by_n(v: dict) -> dict[int, tuple[str, dict]]:
    return {m["n"]: (key, m) for key, m in v["modules"].items()}


def _exercise(v: dict, lab: int, exercise: int) -> dict | None:
    """The `Exercise N` row of lab `lab`'s notebook, or None."""
    found = _module_by_n(v).get(lab)
    if found is None:
        return None
    for r in lab_steps.rows(found[1]["slug"]):
        if r["kind"] == "task" and r["label"] == f"Exercise {exercise}":
            return r
    return None


def _exercise_link(v: dict, lab: int, exercise: int) -> str:
    r = _exercise(v, lab, exercise)
    slug = _module_by_n(v)[lab][1]["slug"]
    url = f"{v['repo']['colab_base']}/{slug}.ipynb"
    return f"[Lab {lab}, Exercise {exercise} · {r['title']}]({url})"


def _sections(slug: str) -> dict:
    path = ROOT / "modules" / f"{slug}.qmd"
    return live_plan.read(slug)["sections"] if path.exists() else {}


# ---------------------------------------------------------------- glossary

# A term that starts with a name keeps its capital mid-sentence: "Jev's confidence field".
NAMES = {"Jev's", "Bradley–Terry", "Jev"}


def mid_sentence(term: str) -> str:
    """A term as it reads inside a sentence: "Token" -> "token", but "LoRA (low-rank
    adaptation)", "KL penalty" and "Jev's confidence field" keep their capitals."""
    first = term.split()[0]
    if first in NAMES or any(c.isupper() for c in first[1:]):
        return term
    return term[0].lower() + term[1:]


def terms_of(module_key: str) -> list[dict]:
    """The glossary terms first defined in one module, in the glossary's order."""
    return [t for t in load(GLOSSARY).get("terms") or [] if t.get("module") == module_key]


def glossary_problems(v: dict, data: dict | None = None) -> list[str]:
    data = load(GLOSSARY) if data is None else data
    out: list[str] = []
    terms = data.get("terms") or []
    ids = [t.get("id") for t in terms]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        out.append(f"glossary: the id {dup!r} is used twice")
    for t in terms:
        where = f"glossary term {t.get('id')!r}"
        missing = {"id", "term", "definition", "example", "module"} - set(t)
        if missing:
            out.append(f"{where}: missing {', '.join(sorted(missing))}")
            continue
        if not ID.match(str(t["id"])):
            out.append(f"{where}: an id is lowercase words joined by hyphens")
        m = v["modules"].get(t["module"])
        if m is None:
            out.append(f"{where}: no module {t['module']!r} in _variables.yml")
            continue
        if "section" in t and t["section"] not in _sections(m["slug"]):
            out.append(f"{where}: Module {m['n']} has no section {t['section']}")
        if "lab" in t:
            lab, ex = t["lab"]
            if _exercise(v, lab, ex) is None:
                out.append(f"{where}: Lab {lab} has no Exercise {ex}")
        for other in t.get("see", []):
            if other not in ids:
                out.append(f"{where}: `see` names {other!r}, which is not a term")
    for s in data.get("symbols") or []:
        missing = {"symbol", "meaning", "module"} - set(s)
        if missing:
            out.append(f"glossary symbol {s.get('symbol')!r}: missing {', '.join(missing)}")
        elif s["module"] not in v["modules"]:
            out.append(f"glossary symbol {s['symbol']!r}: no module {s['module']!r}")
    return out


def glossary(v: dict, data: dict | None = None) -> str:
    data = load(GLOSSARY) if data is None else data
    terms = sorted(data.get("terms") or [], key=lambda t: t["term"].lower())
    by_id = {t["id"]: t for t in terms}
    letters: dict[str, list[dict]] = {}
    for t in terms:
        letters.setdefault(t["term"][0].upper(), []).append(t)
    out = [
        "::: {.glossary-letters}",
        " · ".join(f"[{c}](#letter-{c.lower()})" for c in letters) + " · [Notation](#notation)",
        ":::",
        "",
        "## Terms {#terms}",
    ]
    for letter, group in letters.items():
        out += ["", f"### {letter} {{#letter-{letter.lower()}}}", ""]
        for t in group:
            m = v["modules"][t["module"]]
            where = f"[Module {m['n']} · {m['title']}](/modules/{m['slug']}.qmd)"
            if "section" in t:
                where += f", section {t['section']}"
            facts = [f"First defined in {where}"]
            if "lab" in t:
                facts.append("In the lab: " + _exercise_link(v, *t["lab"]))
            if t.get("see"):
                facts.append(
                    "See also: "
                    + ", ".join(f"[{mid_sentence(by_id[i]['term'])}](#{i})" for i in t["see"])
                )
            out += [
                f"[**{t['term']}**]{{#{t['id']}}}",
                f":   {t['definition'].strip()}",
                "",
                f"    *Example.* {t['example'].strip()}",
                "",
                "    " + " · ".join(facts) + ".",
                "",
            ]
    out += [
        "## Notation {#notation}",
        "",
        "Scalars are italic lowercase, vectors bold or with an arrow where the module says"
        " so, and matrices capital; each module page has its own notation table. Where one"
        " letter means two things, the note says which module means which.",
        "",
        "| Symbol | Meaning | First used | Note |",
        "|---|---|---|---|",
    ]
    for s in data.get("symbols") or []:
        m = v["modules"][s["module"]]
        first = f"[Module {m['n']}](/modules/{m['slug']}.qmd)"
        note = s.get("note", "").strip() or "—"
        meaning = s["meaning"].strip()
        out.append(f"| {s['symbol']} | {meaning} | {first} | {note} |".replace("\n", " "))
    return "\n".join(out)


# ---------------------------------------------------------------- worksheet


def worksheet_problems(v: dict, data: dict | None = None) -> list[str]:
    data = load(WORKSHEET) if data is None else data
    out: list[str] = []
    groups = data.get("groups") or []
    ids = [g.get("id") for g in groups]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        out.append(f"worksheet: the group id {dup!r} is used twice")
    for g in groups:
        where = f"worksheet group {g.get('id')!r}"
        missing = {"id", "title", "compare", "rows"} - set(g)
        if missing:
            out.append(f"{where}: missing {', '.join(sorted(missing))}")
            continue
        if not ID.match(str(g["id"])):
            out.append(f"{where}: an id is lowercase words joined by hyphens")
        for i, r in enumerate(g["rows"], 1):
            row = f"{where}, row {i}"
            need = {"lab", "model", "dataset", "split", "unit", "metric", "direction", "baseline"}
            if need - set(r):
                out.append(f"{row}: missing {', '.join(sorted(need - set(r)))}")
                continue
            if r["lab"] not in _module_by_n(v):
                out.append(f"{row}: no Lab {r['lab']}")
            elif "exercise" in r and _exercise(v, r["lab"], r["exercise"]) is None:
                out.append(f"{row}: Lab {r['lab']} has no Exercise {r['exercise']}")
            if r["dataset"] != GENERATED and r["dataset"] not in v["datasets"]:
                out.append(f"{row}: no dataset {r['dataset']!r} in _variables.yml")
            if r["direction"] not in ("lower", "higher"):
                out.append(f"{row}: direction is lower or higher")
    return out


def _dataset_name(v: dict, r: dict) -> str:
    if r["dataset"] == GENERATED:
        return f"generated in Lab {r['lab']}"
    return v["datasets"][r["dataset"]]["name"]


def _lab_cell(v: dict, r: dict) -> str:
    slug = _module_by_n(v)[r["lab"]][1]["slug"]
    url = f"{v['repo']['colab_base']}/{slug}.ipynb"
    text = f"Lab {r['lab']}" + (f", Ex. {r['exercise']}" if "exercise" in r else "")
    return f"[{text}]({url})"


def worksheet(v: dict, data: dict | None = None) -> str:
    data = load(WORKSHEET) if data is None else data
    out = []
    for g in data.get("groups") or []:
        out += ["", f"## {g['title']} {{#{g['id']}}}", "", f"**Comparable.** {g['compare']}"]
        if g.get("caution"):
            out += ["", f"**Do not compare.** {g['caution']}"]
        out += [
            "",
            "::: {.worksheet}",
            "| Lab | Model | Data, split and unit | Metric | Baseline | Your result | Path |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in g["rows"]:
            data_cell = f"{_dataset_name(v, r)}, {r['split']}, per {r['unit']}"
            metric = f"{r['metric']} ({r['direction']} is better)"
            cells = [_lab_cell(v, r), r["model"], data_cell, metric, r["baseline"], " ", " "]
            out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |")
        out.append(":::")
    return "\n".join(out).lstrip("\n")


def worksheet_csv(v: dict, data: dict | None = None) -> str:
    data = load(WORKSHEET) if data is None else data
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLUMNS)
    for g in data.get("groups") or []:
        for r in g["rows"]:
            w.writerow(
                [
                    g["id"],
                    r["lab"],
                    r.get("exercise", ""),
                    r["model"],
                    _dataset_name(v, r),
                    r["split"],
                    r["unit"],
                    r["metric"],
                    r["direction"],
                    r["baseline"],
                    r.get("seed", ""),
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
    return buf.getvalue()
