"""The glossary (_glossary.yml) and the results worksheet (_worksheet.yml): every module,
section, exercise, dataset and cross-reference they name exists, the generated files are
current, and the worksheet holds no results."""

import csv
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_tables as g  # noqa: E402
import learner_pages as lp  # noqa: E402

V = g.load_variables()


def committed(name: str) -> str:
    text = (ROOT / "_includes" / name).read_text(encoding="utf-8")
    return text.split("\n\n", 1)[1]


class Glossary(unittest.TestCase):
    def test_every_reference_exists(self):
        self.assertEqual(lp.glossary_problems(V), [])

    def test_the_page_is_current_and_linked(self):
        self.assertEqual(committed("glossary.md"), lp.glossary(V).rstrip() + "\n")
        page = (ROOT / "glossary.qmd").read_text(encoding="utf-8")
        self.assertIn("{{< include /_includes/glossary.md >}}", page)
        self.assertIn("glossary.qmd", (ROOT / "references.qmd").read_text(encoding="utf-8"))

    def test_each_module_links_the_terms_it_defines(self):
        for key, m in g.modules_in_order(V):
            terms = lp.terms_of(key)
            block = g.module_block(V, key, m)
            with self.subTest(m["slug"]):
                for t in terms:
                    self.assertIn(f"(/glossary.qmd#{t['id']})", block)

    def test_terms_read_naturally_mid_sentence(self):
        self.assertEqual(lp.mid_sentence("Token"), "token")
        self.assertEqual(lp.mid_sentence("N-gram model"), "n-gram model")
        self.assertEqual(
            lp.mid_sentence("LoRA (low-rank adaptation)"), "LoRA (low-rank adaptation)"
        )
        self.assertEqual(lp.mid_sentence("KL penalty"), "KL penalty")
        self.assertEqual(lp.mid_sentence("Jev's confidence field"), "Jev's confidence field")

    def test_problems_are_found(self):
        data = {
            "terms": [
                {"id": "a", "term": "A", "definition": "d", "example": "e", "module": "m01"},
                {"id": "a", "term": "B", "definition": "d", "example": "e", "module": "m99"},
                {
                    "id": "Bad Id",
                    "term": "C",
                    "definition": "d",
                    "example": "e",
                    "module": "m01",
                    "section": 99,
                    "lab": [1, 99],
                    "see": ["nowhere"],
                },
            ],
            "symbols": [{"symbol": "$x$", "meaning": "m", "module": "m99"}],
        }
        found = "\n".join(lp.glossary_problems(V, data))
        for expected in [
            "used twice",
            "m99",
            "lowercase",
            "no section 99",
            "no Exercise 99",
            "nowhere",
        ]:
            self.assertIn(expected, found)


class Worksheet(unittest.TestCase):
    def test_every_reference_exists(self):
        self.assertEqual(lp.worksheet_problems(V), [])

    def test_the_page_and_the_csv_are_current(self):
        self.assertEqual(committed("worksheet.md"), lp.worksheet(V).rstrip() + "\n")
        self.assertEqual(lp.WORKSHEET_CSV.read_text(encoding="utf-8"), lp.worksheet_csv(V))

    def test_the_csv_holds_no_results(self):
        rows = list(csv.DictReader(io.StringIO(lp.worksheet_csv(V))))
        self.assertTrue(rows)
        for row in rows:
            for column in ("result", "path", "environment", "seconds", "interpretation"):
                self.assertEqual(row[column], "", (row["group"], column))

    def test_each_group_keeps_one_metric_and_unit(self):
        # A comparison group compares like with like (suggestions.md, item 10).
        for group in lp.load(lp.WORKSHEET).get("groups", []):
            pairs = {(r["unit"], r["metric"], r["direction"]) for r in group["rows"]}
            metrics = {m for _, m, _ in pairs}
            with self.subTest(group["id"]):
                self.assertTrue(group["rows"])
                for metric in metrics:
                    units = {u for u, m, _ in pairs if m == metric}
                    self.assertEqual(len(units), 1, f"{metric} is averaged over {units}")


if __name__ == "__main__":
    unittest.main()
