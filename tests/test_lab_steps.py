"""scripts/lab_steps.py reads every lab's task list from its notebook.

The generated `_includes/lab-NN.md` is only as good as these patterns: a heading style
the patterns miss drops a task or a whole challenge from the module page silently, and
the drift gate cannot see it because the generator agrees with itself.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lab_steps as L  # noqa: E402

V = yaml.safe_load((ROOT / "_variables.yml").read_text(encoding="utf-8"))
LABS = [
    m
    for m in sorted(V["modules"].values(), key=lambda x: x["n"])
    if m.get("notebook", True) and (ROOT / "notebooks" / f"{m['slug']}.ipynb").exists()
]


def markdown_headings(slug: str) -> list[str]:
    cells = json.loads((ROOT / "notebooks" / f"{slug}.ipynb").read_text(encoding="utf-8"))["cells"]
    return [
        line
        for c in cells
        if c["cell_type"] == "markdown"
        for line in "".join(c["source"]).splitlines()
        if line.startswith("#")
    ]


class Rows(unittest.TestCase):
    def test_every_lab_has_parts_and_tasks(self):
        for m in LABS:
            found = L.rows(m["slug"])
            kinds = {r["kind"] for r in found}
            self.assertIn("part", kinds, m["slug"])
            self.assertIn("task", kinds, m["slug"])

    def test_every_stretch_section_becomes_a_challenge(self):
        # Lab 13 writes its stretch as `#`, the others as `##`: both must be found.
        for m in LABS:
            has = any(
                re.match(r"^#+\s+Stretch\s*\(optional\)", line)
                for line in markdown_headings(m["slug"])
            )
            got = L.challenge(L.rows(m["slug"])) is not None
            self.assertEqual(has, got, m["slug"])

    def test_every_exercise_heading_becomes_a_task(self):
        for m in LABS:
            headings = [
                line for line in markdown_headings(m["slug"]) if re.match(r"^#+\s+Exercise\s", line)
            ]
            tasks = [r for r in L.rows(m["slug"]) if r["label"].startswith("Exercise")]
            self.assertEqual(len(headings), len(tasks), m["slug"])

    def test_stated_minutes_are_read(self):
        for m in LABS:
            for r in L.rows(m["slug"]):
                if r["kind"] == "task" and r["minutes"] is not None:
                    self.assertGreater(r["minutes"], 0, (m["slug"], r["label"]))


class Table(unittest.TestCase):
    def test_no_part_row_without_tasks_under_it(self):
        # Lab 15's "Part C · Evaluate and share" has no exercise of its own.
        for m in LABS:
            rows = L.table(L.rows(m["slug"])).splitlines()[2:]
            for i, line in enumerate(rows):
                if line.startswith("| **Part"):
                    rest = rows[i + 1 :]
                    following = next((r for r in rest if not r.startswith("| **Part")), None)
                    self.assertIsNotNone(following, (m["slug"], line))

    def test_the_challenge_is_not_in_the_table(self):
        for m in LABS:
            self.assertNotIn("Challenge", L.table(L.rows(m["slug"])), m["slug"])


class Generated(unittest.TestCase):
    def test_each_lab_include_matches_its_notebook(self):
        for m in LABS:
            include = (ROOT / "_includes" / f"lab-{m['n']:02d}.md").read_text(encoding="utf-8")
            for r in L.rows(m["slug"]):
                if r["kind"] == "task":
                    self.assertIn(f"{r['label']} · {r['title']}", include, m["slug"])

    def test_each_module_page_includes_its_lab(self):
        for m in LABS:
            page = (ROOT / "modules" / f"{m['slug']}.qmd").read_text(encoding="utf-8")
            self.assertIn(f"/_includes/lab-{m['n']:02d}.md", page, m["slug"])


if __name__ == "__main__":
    unittest.main()
