"""Build images/social-preview.png: the card GitHub shows when the repo is linked.

GitHub's social preview is 1280x640. The colors are the site's own (custom.scss:
$nl-navy, $nl-accent, $nl-on-navy), and the numbers come from _variables.yml and the
notebooks, through gen_tables.py, so the card cannot claim a module or an exercise the
workshop does not have.

Run:   python scripts/make_social_preview.py
Upload: GitHub -> Settings -> General -> Social preview -> Edit -> Upload an image.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gen_tables as g  # noqa: E402

OUT = ROOT / "images" / "social-preview.png"
W, H = 1280, 640

# custom.scss, the dark palette of custom-dark.scss for the background.
NAVY = (18, 38, 58)
INK = (255, 255, 255)
MUTED = (154, 168, 184)
ACCENT = (214, 122, 63)
RULE = (44, 66, 90)

# The site ships Inter and Source Serif 4 as woff2, which Pillow cannot read; these are
# the nearest faces installed on macOS. The first that loads wins.
FACES = {
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf"],
    "regular": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"],
}


def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FACES[weight]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise SystemExit(f"no {weight} font found; add one to FACES")


def facts(v: dict) -> str:
    labs = sum(1 for m in v["modules"].values() if g.has_notebook(m)) + 1  # plus 00-setup
    taught = [m for m in v["modules"].values() if not g.is_prework(m)]
    return (
        f"{v['workshop']['days']} days   ·   {len(taught)} modules   ·   "
        f"{labs} Colab notebooks   ·   {g.exercise_count(v)} hands-on exercises"
    )


def main() -> None:
    v = g.load_variables()
    w = v["workshop"]
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)

    # An accent rule down the left edge, the way the module header carries one on top.
    d.rectangle([0, 0, 10, H], fill=ACCENT)

    x = 86
    d.text(
        (x, 108), f"{w['org'].upper()}   ·   FIVE-DAY WORKSHOP", font=font("bold", 23), fill=ACCENT
    )

    # The title wraps by hand: two lines, broken where the sense breaks.
    d.text((x, 170), "From Traditional NLP", font=font("bold", 76), fill=INK)
    d.text((x, 258), "to Modern LLMs", font=font("bold", 76), fill=INK)

    d.text((x, 372), w["subtitle"], font=font("regular", 34), fill=MUTED)

    d.line([(x, 466), (W - 86, 466)], fill=RULE, width=2)
    d.text((x, 500), facts(v), font=font("bold", 25), fill=INK)
    d.text(
        (x, 548),
        v["repo"]["site_url"].replace("https://", ""),
        font=font("regular", 22),
        fill=MUTED,
    )

    OUT.parent.mkdir(exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB, {W}x{H})")


if __name__ == "__main__":
    main()
