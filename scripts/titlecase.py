"""Title case for titles and headings (CONTRIBUTING.md, "Capitalization").

The rule is APA title case. Capitalize the first word, the first word after a colon, a
dash or a middle dot, and every other word except the short function words in MINOR
(articles, and conjunctions and prepositions of three letters or fewer). Capitalize each
part of a hyphenated word except a short function word inside it ("Fine-Tuning",
"Sequence-to-Sequence"). Words of four letters or more are capitalized whatever they are
("With", "From", "Into").

Left as written: a word with a capital letter after its first (LoRA, PyTorch, macOS), a
lowercase name or symbol in KEEP (uv, top-k), a version tag (v1), code, math, links'
targets, shortcodes, a heading's attributes, and parentheticals, which are notes rather
than title ("(8 minutes)", "(optional)").

tests/test_style.py checks every heading with `title_case(text) == text`. Python's
`str.title()` is not used: it breaks LoRA, Recall@k and Lab 8's.
"""

from __future__ import annotations

import re

MINOR = {
    # articles
    "a", "an", "the",
    # short conjunctions
    "and", "as", "but", "for", "if", "nor", "or", "so", "yet",
    # short prepositions
    "at", "by", "in", "of", "off", "on", "per", "to", "via", "vs.",
}  # fmt: skip

# Lowercase names and symbols that keep their spelling in a title.
KEEP = {"uv", "pip", "k", "e.g.", "i.e."}

# Spans that are not words: code, math, shortcodes, attributes, a link's target,
# HTML tags and comments, and parentheticals (notes, not title).
_PROTECT = re.compile(
    r"`[^`]*`"
    r"|\$[^$]*\$"
    r"|\{\{<.*?>\}\}"
    r"|\{[^}]*\}"
    r"|\]\([^)]*\)"
    r"|<!--.*?-->|<[^>]+>"
    r"|\((?:[^()]|\([^()]*\))*\)"
)
# A separator after which a new phrase starts: colon, question or exclamation mark,
# semicolon, an em dash, a spaced en dash, or a middle dot. A full stop ends a sentence
# too, unless it ends an abbreviation such as "vs.".
_BREAK = re.compile(r"[:?!;]$|^[—·–]$|—$")
_LETTER = re.compile(r"[A-Za-z]")
# A version tag keeps its lowercase v: "arXiv Topics v1".
_VERSION = re.compile(r"^v\d+(?:\.\d+)*$")
# A single capital letter is a label ("Part A", "Stretch A"), never the article.
_LABEL = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _element(part: str, start: bool) -> str:
    """One hyphen-separated piece of a word, in title case. `start` capitalizes it even
    when it is a short function word."""
    m = _LETTER.search(part)
    if m is None or part[0].isdigit():
        return part
    i = m.start()
    head, core = part[:i], part[i:]
    bare = core.rstrip(".,:;?!’'\"”*_")
    if bare in KEEP or bare.lower() in KEEP or _VERSION.match(bare):
        return part
    if any(c.isupper() for c in core[1:]) or core.rstrip(".,:;") in _LABEL:
        return part  # a name, an acronym or a label: LoRA, PyTorch, macOS, RLHF, Part A
    lower = core.lower()
    if not start and (bare.lower() in MINOR or lower in MINOR):
        return head + lower
    return head + core[0].upper() + core[1:]


def _word(word: str, start: bool) -> str:
    """A whitespace-separated word: each part of a hyphenated or slashed word in turn.

    The first and last parts of a hyphenated word are capitalized even when they are
    short function words ("Off-Policy", "Trade-Off"); a function word inside it is not
    ("Sequence-to-Sequence", "Human-in-the-Loop")."""
    parts = re.split(r"([-–/])", word)
    count = len(parts[::2])
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append(part)  # the separator
            continue
        k = i // 2
        out.append(_element(part, start if count == 1 else k in (0, count - 1)))
    return "".join(out)


def title_case(text: str) -> str:
    """`text` in title case, with the protected spans unchanged."""
    spans: list[str] = []

    def stash(m: re.Match) -> str:
        spans.append(m.group(0))
        # \x01 marks a note (a parenthetical, attributes, a comment): it is not a word.
        mark = "\x01" if m.group(0)[0] in "({<" and not m.group(0).startswith("{{<") else "\x00"
        return f"{mark}{len(spans) - 1}{mark}"

    masked = _PROTECT.sub(stash, text)
    pieces = re.split(r"(\s+)", masked)

    def plain(piece: str) -> str:
        return re.sub(r"[\x00\x01]\d+[\x00\x01]", "", piece)

    # The last word, counting numbers and code but not notes: "Days 2 to 5".
    words = [i for i, p in enumerate(pieces) if re.search(r"\w", re.sub(r"\x01\d+\x01", "", p))]
    last = words[-1] if words else -1
    out = []
    start = True
    for n, piece in enumerate(pieces):
        if not piece or piece.isspace():
            out.append(piece)
            continue
        bare = plain(piece)
        if not _LETTER.search(bare):
            out.append(piece)
            if "\x00" in piece:
                start = False  # code or math on its own counts as a word
            elif _BREAK.search(bare):
                start = True  # "·", "—"
            # A number or a note keeps the position: "1. The Markov Assumption".
            continue
        # The last word is capitalized too: "Who It Is For".
        out.append(_word(piece, start or n == last))
        start = bool(_BREAK.search(bare)) or (
            bare.endswith(".") and bare.rstrip(".,").lower() + "." not in MINOR | KEEP
        )
    result = "".join(out)
    return re.sub(r"[\x00\x01](\d+)[\x00\x01]", lambda m: spans[int(m.group(1))], result)


def heading_text(line: str) -> str:
    """The text of a markdown heading line, without its hashes."""
    return re.sub(r"^#{1,6}\s+", "", line.rstrip())
