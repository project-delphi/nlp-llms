"""Published prose uses American spelling, and titles and headings use title case
(AGENTS.md, "Language"; CONTRIBUTING.md, "Style").

Checks the sources of everything a participant reads: the rendered pages, the notebooks'
hand-written cells, _variables.yml and the generators that write pages and notebook cells.
Generated files are not checked; their sources are. Fenced and inline code, URLs and HTML
comments are skipped, and so are the phrases in ALLOWED (quotations and cited titles).
"""

import json
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from titlecase import title_case  # noqa: E402

SOURCES = [
    "*.qmd",
    "modules/*.qmd",
    "prepare/*.md",
    "facilitator-guide.md",
    "instructor-pace.md",
    "knowledge-checks.md",
    "README.md",
    "CONTRIBUTING.md",
    "data/README.md",
    "_variables.yml",
    "notebooks/*.ipynb",
    "scripts/gen_*.py",
    "scripts/harness.py",
    # The glossary, the worksheet and the reading guides on every module page.
    "_glossary.yml",
    "_worksheet.yml",
    "scripts/learner_pages.py",
    "scripts/live_plan.py",
]

# British spelling -> what to write instead. Stems cover the -ise/-isation families; the
# list is short on purpose: words that are common in this workshop's subject.
_ISE = (
    "optimi|normali|tokeni|initiali|organi|recogni|summari|minimi|maximi|generali|visuali|"
    "regulari|seriali|penali|utili|categori|characteri|randomi|standardi|speciali|emphasi|"
    "memori|vectori|parameteri|finali|customi|authori|reali|prioriti"
)
BRITISH = re.compile(
    r"\b(?:"
    r"label{2}(?:ed|ing)|model{2}(?:ed|ing)|travel{2}(?:ed|ing)|"
    r"behaviours?|colour(?:s|ed|ing)?|centres?|centred|favour(?:s|ed|ing|able|ite|ites)?|"
    r"analys(?:e|ed|ing)|artefacts?|judgements?|catalogues?|programmes?|"
    rf"(?:{_ISE})(?:se|sed|ses|sing|ser|sers|sation|sations)"
    r")\b",
    re.IGNORECASE,
)

# Quotations and cited titles keep their own spelling.
ALLOWED = [
    "Understanding the Effects of RLHF on LLM Generalisation and Diversity",
]

_FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
_INLINE = re.compile(r"`[^`\n]*`")
_URL = re.compile(r"https?://\S+")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def prose(text):
    """Text with code, URLs, HTML comments and allowed phrases removed."""
    for phrase in ALLOWED:
        text = text.replace(phrase, "")
    for pattern in (_COMMENT, _FENCE, _INLINE, _URL):
        text = pattern.sub(" ", text)
    return text


def texts(path):
    """(label, text) pairs to check in one source file."""
    if path.suffix == ".ipynb":
        cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
        for i, cell in enumerate(cells):
            if "generated" in cell.get("metadata", {}).get("tags", []):
                continue  # written by scripts/gen_notebooks.py, which is checked itself
            source = "".join(cell["source"])
            # A markdown cell is prose; in a code cell, comments and strings are what people read.
            yield (
                f"cell {i}",
                prose(source) if cell["cell_type"] == "markdown" else _URL.sub(" ", source),
            )
    else:
        yield "", prose(path.read_text(encoding="utf-8"))


class AmericanSpelling(unittest.TestCase):
    def test_published_prose_uses_american_spelling(self):
        for pattern in SOURCES:
            for path in sorted(ROOT.glob(pattern)):
                for where, text in texts(path):
                    found = sorted({m.group(0) for m in BRITISH.finditer(text)})
                    with self.subTest(path=str(path.relative_to(ROOT)), where=where):
                        self.assertEqual(
                            found, [], "use American spelling (CONTRIBUTING.md, Style)"
                        )

    def test_pattern_catches_british_and_passes_american(self):
        for word in [
            "labelled",
            "Labelling",
            "modelling",
            "behaviour",
            "colour",
            "centre",
            "favour",
            "analysed",
            "normalise",
            "tokenisation",
            "optimiser",
            "judgement",
        ]:
            self.assertIsNotNone(BRITISH.search(word), word)
        for word in [
            "labeled",
            "modeling",
            "behavior",
            "color",
            "center",
            "favor",
            "analysis",
            "analyses",
            "normalize",
            "tokenization",
            "optimizer",
            "judgment",
            "exercise",
            "precise",
            "noise",
            "otherwise",
            "promise",
            "rise",
            "concise",
        ]:
            self.assertIsNone(BRITISH.search(word), word)

    def test_code_urls_and_cited_titles_are_skipped(self):
        self.assertNotRegex(prose("see `normalise()` at https://x.org/colour"), BRITISH)
        self.assertNotRegex(prose("```python\ncolour = 1\n```\n"), BRITISH)
        self.assertNotRegex(prose(ALLOWED[0]), BRITISH)


# Where titles and headings are written. Generated files are checked here too: their
# headings come from the generators' own strings as well as from _variables.yml.
HEADING_SOURCES = [
    "*.qmd",
    "modules/*.qmd",
    "prepare/*.md",
    "_includes/*.md",
    "facilitator-guide.md",
    "instructor-pace.md",
    "knowledge-checks.md",
    "README.md",
]
_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$")
_CALLOUT_TITLE = re.compile(r'^\s*:::.*\btitle="([^"]*)"')
_FRONT_TITLE = re.compile(r'^(?:title|subtitle):\s*["\']?(.*?)["\']?\s*$')


def markdown_titles(text):
    """(line number, title) for each heading, callout title and front-matter title,
    outside fenced code."""
    lines = text.split("\n")
    front = bool(lines) and lines[0] == "---"
    fence = None
    for i, line in enumerate(lines, 1):
        if front:
            if i > 1 and line == "---":
                front = False
            elif i > 1 and (m := _FRONT_TITLE.match(line)):
                yield i, m.group(1)
            continue
        if m := re.match(r"^\s*(`{3,}|~{3,})", line):
            fence = None if fence and m.group(1).startswith(fence) else fence or m.group(1)
            continue
        if fence:
            continue
        if m := _HEADING.match(line):
            yield i, m.group(1)
        elif m := _CALLOUT_TITLE.match(line):
            yield i, m.group(1)


def variable_titles():
    """(key, title) for the titles and labels in _variables.yml that pages show as titles."""
    v = yaml.safe_load((ROOT / "_variables.yml").read_text(encoding="utf-8"))
    yield "workshop.title", v["workshop"]["title"]
    yield "workshop.subtitle", v["workshop"]["subtitle"]
    yield "setup.title", v["setup"]["title"]
    for key, m in v["modules"].items():
        yield f"modules.{key}.title", m["title"]
    for key, d in v["days"].items():
        for field in ("title", "short", "opening", "closing"):
            if field in d:
                yield f"days.{key}.{field}", d[field]
        if "clinic" in d:
            yield f"days.{key}.clinic.label", d["clinic"]["label"]
        for slot in d["slots"]:
            if isinstance(slot, dict) and "label" in slot:
                yield f"days.{key}.slots", slot["label"]


def navigation_titles():
    """(file, text) for each navbar, footer and sidebar entry."""
    for name in ("_quarto.yml", "_includes/sidebar.yml"):
        for m in re.finditer(
            r"^\s*-?\s*(?:text|section):\s*[\"']?(.*?)[\"']?\s*$",
            (ROOT / name).read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            yield name, m.group(1)


class TitleCase(unittest.TestCase):
    def assertTitleCase(self, title, where):
        with self.subTest(where=where):
            self.assertEqual(title, title_case(title), "use title case (CONTRIBUTING.md, Style)")

    def test_headings_and_page_titles(self):
        for pattern in HEADING_SOURCES:
            for path in sorted(ROOT.glob(pattern)):
                for line, title in markdown_titles(path.read_text(encoding="utf-8")):
                    self.assertTitleCase(title, f"{path.relative_to(ROOT)}:{line}")

    def test_notebook_headings(self):
        for path in sorted(ROOT.glob("notebooks/*.ipynb")):
            cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
            for i, cell in enumerate(cells):
                if cell["cell_type"] == "markdown":
                    for _, title in markdown_titles("".join(cell["source"])):
                        self.assertTitleCase(title, f"{path.relative_to(ROOT)} cell {i}")

    def test_titles_in_variables_and_navigation(self):
        for where, title in [*variable_titles(), *navigation_titles()]:
            self.assertTitleCase(title, where)

    def test_rule(self):
        cases = [
            ("Text as data", "Text as Data"),
            ("Pretraining and the Hugging Face stack", "Pretraining and the Hugging Face Stack"),
            ("Scaled dot-product attention", "Scaled Dot-Product Attention"),
            ("Fine-tuning and LoRA", "Fine-Tuning and LoRA"),
            ("Counting n-grams and add-k smoothing", "Counting N-Grams and Add-k Smoothing"),
            ("The human-in-the-loop driver", "The Human-in-the-Loop Driver"),
            ("Stretch (optional) · Top-$k$ sampling", "Stretch (optional) · Top-$k$ Sampling"),
            ("Exercise 1 · Tokens (8 minutes)", "Exercise 1 · Tokens (8 minutes)"),
            ("Parse a raw response into a `Reply`", "Parse a Raw Response Into a `Reply`"),
            ("1. The zero problem {#zero}", "1. The Zero Problem {#zero}"),
            ("Part A · Recurrent networks", "Part A · Recurrent Networks"),
            ("Who it is for", "Who It Is For"),
            ("The reward–drift trade-off", "The Reward–Drift Trade-Off"),
            ("Lab 8's provider wrapper, restated", "Lab 8's Provider Wrapper, Restated"),
            ("Recall@k and reciprocal rank", "Recall@k and Reciprocal Rank"),
            ("Calling `generate`: the basics", "Calling `generate`: The Basics"),
            ("Why $p$: the intuition", "Why $p$: The Intuition"),
            (
                "Classification: arXiv Topics v1, test split",
                "Classification: arXiv Topics v1, Test Split",
            ),
            ("Optional: setup with uv on macOS", "Optional: Setup With uv on macOS"),
            ("When the clock slips on Days 2 to 5", "When the Clock Slips on Days 2 to 5"),
            (
                "Module 1 · {{< var modules.m01.title >}}",
                "Module 1 · {{< var modules.m01.title >}}",
            ),
        ]
        for before, after in cases:
            self.assertEqual(title_case(before), after)
            self.assertEqual(title_case(after), after, "title_case is idempotent")


if __name__ == "__main__":
    unittest.main()
