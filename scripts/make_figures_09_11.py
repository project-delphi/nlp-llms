"""Write the figures of Modules 9-11 as hand-laid-out SVG.

  images/09-text-as-mdp.svg        text generation as a sequence of decisions (Module 9, section 2)
  images/09-baseline-variance.svg  REINFORCE estimates with and without a baseline (section 4)
  images/09-reward-model.svg       the reward model and its pairwise loss (section 8)
  images/10-rlhf-pipeline.svg      the three stages of RLHF (Module 10, section 2)
  images/10-reward-drift.svg       proxy and gold reward against drift (section 7)
  images/11-reliability.svg        reliability diagrams before and after temperature scaling
                                   (Module 11, section 3)
  images/11-risk-coverage.svg      the risk-coverage curve and Chow's threshold (section 8)

Three figures are measured; nothing in them is invented or smoothed.

- 09-baseline-variance.svg is drawn from images/09-baseline-variance.json, which Lab 9 writes in
  Exercise 2: K = 500 one-batch REINFORCE estimates (N = 16) of one coordinate of the gradient at
  the uniform policy, without a baseline and with the leave-one-out baseline, and the exact value
  from exact_gradient(theta). The standard deviations in the figure are read from that file.
- 11-reliability.svg and 11-risk-coverage.svg are drawn from images/11-calibration.json, which
  `--measure` writes by rerunning the Lab 1 classifier path of Lab 11 (the notebook's tokenizer,
  CountVectorizer(min_df=2), TfidfTransformer(), LogisticRegression(C, max_iter=1000,
  random_state=0), its fit_temperature, reliability_bins and risk_coverage) on
  data/arxiv_topics_v1.csv.gz. Lab 11 does not save per-bin statistics, so they were recomputed
  on 2026-10-08 on the build Mac's CPU (scikit-learn 1.9.1, NumPy 2.5.3, SciPy 1.18.1). Every
  summary number matches the build-container run of 2026-10-05 in briefs/11-calibration.md:
  C = 1 test ECE 0.1641, tau* 0.468, ECE after 0.0094; C = 10 error rate 0.11625, Chow's rule at
  lambda = 0.9 coverage 0.578 and risk 0.0216. The drawing step asserts the ones it prints.

The other four are schematics. 10-reward-drift.svg has no numbers on its axes: it draws the
shape Gao et al. (2023) report, not a measurement. Redraw it from Lab 10's stretch sweep
(reward_drift_points.json, written by `scripts/lab10_seed_protocol.py summarize`) once that has
run on a T4.

The palette, the style block and the drawing helpers are imported from make_figures_05_08.py, so
the figures of Modules 5 to 11 share one look. Output is deterministic: running the script twice
gives identical files.

Run:  python scripts/make_figures_09_11.py
          draws the seven figures (standard library only)
      uv run --group execute python scripts/make_figures_09_11.py --measure
          first recomputes images/11-calibration.json (needs NumPy, SciPy, scikit-learn)
"""

# SVG markup and the alt-text strings are kept on one line each, so they read as they appear
# in the output.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from xml.sax.saxutils import escape

from make_figures_05_08 import (
    ACCENT,
    DIM,
    IMAGES,
    INK,
    MUTED,
    NAVY,
    PALE,
    M,
    dot,
    f,
    line,
    mix,
    path,
    rect,
    svg,
    text,
)

ROOT = IMAGES.parent
CALIBRATION = IMAGES / "11-calibration.json"
GRAY_FILL, GRAY_EDGE = "#d5dbe2", "#7b8794"  # "no baseline" bars: gray, as the spec asks
ACC_FILL = mix(ACCENT, "#ffffff", 0.55)


def poly(points: list[tuple[float, float]]) -> str:
    """An SVG path through the points, coordinates rounded to 0.1 px."""
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)


def vtext(x: float, y: float, s: str, cls: str = "note") -> str:
    """Text rotated to read upward, centered on (x, y)."""
    return f'<text transform="translate({f(x)},{f(y)}) rotate(-90)" text-anchor="middle" class="{cls}">{escape(s)}</text>'


def fmt_tick(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("0", "-0") else s.replace("-", "−")


# ===================================================================== Module 9


def fig_text_as_mdp() -> str:
    W, H = 760, 268
    yc, bh = 120, 44  # state row: center and box height
    tokens = [[], ["y_1"], ["y_1", "y_2"], ["y_1", "y_2", "y_3"]]
    widths = [44, 72, 100, 128]
    gap_in, lm_w, gap_out = 16, 42, 20
    eos_w = 66
    total = sum(widths) + 4 * (gap_in + lm_w + gap_out) + eos_w
    x = (W - total) / 2
    left = x
    b: list[str] = []
    b.append(
        M(
            24,
            32,
            "\\t{Each step: }a_t = y_t ∼ π_θ(· | s_t)\\t{, drawn from the same LM box: one policy, shared by every step}",
            size=15,
            anchor="start",
        )
    )
    rewards = ["r_1 = 0", "r_2 = 0", "r_3 = 0", "r_4 = R(x, y)"]
    for k in range(4):
        w = widths[k]
        b.append(rect(x, yc - bh / 2, w, bh, "box"))
        b.append(M(x + w / 2, yc - bh / 2 - 12, f"s_{k + 1}", size=17))
        # content: the prompt x in gray, then the tokens so far
        cw = 11 + 28 * len(tokens[k])
        cx0 = x + (w - cw) / 2
        b.append(M(cx0, yc + 6, "x", size=19, anchor="start", cls="note"))
        if tokens[k]:
            b.append(M(cx0 + 17, yc + 6, " ".join(tokens[k]), size=19, anchor="start"))
        x += w
        # the action arrow through the shared LM box
        lx = x + gap_in
        b.append(line(x, yc, lx - 1, yc))
        b.append(rect(lx, yc - 14, lm_w, 28, "op", rx=5))
        b.append(text(lx + lm_w / 2, yc + 5, "LM", "mono", size=13))
        b.append(line(lx + lm_w, yc, lx + lm_w + gap_out - 1, yc))
        last = k == 3
        b.append(
            M(
                lx + lm_w / 2,
                yc - 26,
                rewards[k],
                size=15,
                cls="acc" if last else "note",
            )
        )
        if last:
            b.append(M(lx + lm_w / 2 - 6, yc + 38, "a_4 = y_4 =", size=15, anchor="end"))
            b.append(text(lx + lm_w / 2 - 2, yc + 38, "<eos>", "mono", anchor="start", size=13))
        else:
            b.append(M(lx + lm_w / 2, yc + 38, f"a_{k + 1} = y_{k + 1}", size=15))
        x = lx + lm_w + gap_out
    # the end of the episode
    b.append(rect(x, yc - bh / 2, eos_w, bh, "abox"))
    b.append(text(x + eos_w / 2, yc + 5, "<eos>", "mono", size=14))
    b.append(text(x + eos_w / 2, yc - bh / 2 - 12, "end", "note"))
    right = x + eos_w
    # the return
    by = yc + 62
    b.append(path(f"M{f(left)},{by - 7} v7 H{f(right)} v-7", cls="rule", mk=None))
    b.append(
        M(
            (left + right) / 2,
            by + 26,
            "\\t{return }G = r_1 + r_2 + r_3 + r_4 = R(x, y)",
            size=17,
        )
    )
    b.append(
        text(
            (left + right) / 2,
            by + 50,
            "the reward arrives once, at the end: every earlier step gets reward 0",
            "note",
        )
    )
    return svg(
        W,
        H,
        "Text generation as a sequence of decisions",
        "Four state boxes in a row, s_1 to s_4. Each holds the prompt x, in gray, followed by the tokens so far: s_1 holds x, s_2 holds x y_1, s_3 holds x y_1 y_2 and s_4 holds x y_1 y_2 y_3. Between consecutive states an arrow passes through a small box marked LM, the same box at every step: the action a_t = y_t is drawn from pi_theta given s_t. Above the arrows, the rewards r_1 = 0, r_2 = 0 and r_3 = 0. The last arrow, the action a_4 = y_4 = eos, ends in a box marked eos, and its reward, in the accent color, is r_4 = R(x, y). A bracket under the whole strip is labeled: return G = r_1 + r_2 + r_3 + r_4 = R(x, y).",
        b,
    )


def fig_baseline_variance() -> str:
    data = json.loads((IMAGES / "09-baseline-variance.json").read_text(encoding="utf-8"))
    K, N, exact = data["K"], data["N"], data["exact"]
    coord = data["coordinate"]
    series = [
        ("no baseline", data["no_baseline"], data["std"]["no_baseline"], GRAY_FILL, GRAY_EDGE),
        (
            "leave-one-out baseline",
            data["leave_one_out"],
            data["std"]["leave_one_out"],
            ACC_FILL,
            ACCENT,
        ),
    ]
    for _, vals, sd, _, _ in series:
        assert len(vals) == K, "one estimate per batch"
        assert abs(statistics.stdev(vals) - sd) < 1e-5, "the recorded std must match the values"
    # Bins of width 4/768: the no-baseline estimates lie on a lattice of step 1/768 (rewards in
    # sixths, scores 7/8 or -1/8, mean over N = 16), so each bin holds exactly four lattice
    # points and no estimate sits on an edge.
    step = 4 / 768
    lo_v, hi_v = -0.03, 0.105
    k0 = math.floor((lo_v * 768 - 0.5) / 4)
    k1 = math.ceil((hi_v * 768 - 0.5) / 4)
    edges = [(4 * k + 0.5) / 768 for k in range(k0, k1 + 1)]
    for _, vals, _, _, _ in series:
        assert edges[0] < min(vals) and max(vals) < edges[-1], "every estimate is drawn"

    def counts(vals: list[float]) -> list[int]:
        c = [0] * (len(edges) - 1)
        for v in vals:
            c[int((v - edges[0]) // step)] += 1
        return c

    hists = [counts(vals) for _, vals, _, _, _ in series]
    top = max(max(h) for h in hists)
    ymax = 50 * math.ceil(top / 50)
    W, H = 720, 430
    x0, x1 = 86, 690
    sx = (x1 - x0) / (hi_v - lo_v)

    def X(v: float) -> float:
        return x0 + (v - lo_v) * sx

    panels = [(64, 184), (222, 342)]  # (top, bottom) of each panel's plot area
    b: list[str] = []
    for (name, vals, sd, fill, edge), hist, (pt, pb) in zip(series, hists, panels, strict=True):
        ph = pb - pt
        for t in range(0, ymax + 1, 50):
            y = pb - ph * t / ymax
            b.append(line(x0, y, x1, y, cls="rule", mk=None, extra=' style="stroke-width:1"'))
            b.append(text(x0 - 8, y + 4, str(t), "note", anchor="end", size=12))
        for i, c in enumerate(hist):
            if c:
                xa, xb = X(edges[i]), X(edges[i + 1])
                hgt = ph * c / ymax
                b.append(
                    f'<rect x="{xa:.1f}" y="{pb - hgt:.1f}" width="{xb - xa:.1f}" height="{hgt:.1f}" fill="{fill}" stroke="{edge}" stroke-width="1"/>'
                )
        b.append(
            line(x0, pb, x1, pb, cls="ln", mk=None, extra=f' style="stroke:{MUTED};stroke-width:1"')
        )
        mean = statistics.fmean(vals)
        # mean +/- 1 std, drawn above the bars
        ey = pt + 12
        b.append(
            path(
                f"M{X(mean - sd):.1f},{ey - 5} v10 M{X(mean - sd):.1f},{ey} H{X(mean + sd):.1f} M{X(mean + sd):.1f},{ey - 5} v10",
                mk=None,
                extra=f' style="stroke:{edge};stroke-width:2"',
            )
        )
        b.append(dot(X(mean), ey, 3.6, edge))
        b.append(
            text(X(mean + sd) + 8, ey + 5, f"mean ± 1 std: std {sd:.3f}", "note", anchor="start")
        )
        b.append(text(x1, pt + 44, name, "b", anchor="end", size=15))
        b.append(text(x1, pt + 62, f"{K} batches of N = {N}", "note", anchor="end"))
    b.append(vtext(24, (panels[0][0] + panels[1][1]) / 2, f"batches (of {K}) per bin"))
    # the exact gradient, across both panels
    ex = X(exact)
    b.append(
        line(
            ex,
            50,
            ex,
            panels[1][1],
            cls="ln",
            mk=None,
            extra=f' style="stroke:{INK};stroke-width:1.5;stroke-dasharray:5 3"',
        )
    )
    b.append(text(ex, 42, f"exact gradient {exact:.4f}", "note b", size=13.5))
    # x axis
    yb = panels[1][1]
    for v in (-0.02, 0.0, 0.02, 0.04, 0.06, 0.08, 0.10):
        b.append(
            line(
                X(v),
                yb,
                X(v),
                yb + 5,
                cls="ln",
                mk=None,
                extra=f' style="stroke:{MUTED};stroke-width:1"',
            )
        )
        b.append(text(X(v), yb + 20, fmt_tick(v), "note", size=12))
    b.append(
        M(
            (x0 + x1) / 2,
            yb + 44,
            f"\\t{{one-batch estimate of }}∂J / ∂θ[{coord['t']}, \\t{{BOS}}, {coord['action']}]\\t{{: step 1, the target's first symbol}}",
            size=15,
        )
    )
    b.append(
        text(
            W - 16,
            H - 12,
            f"measured: Lab 9, Exercise 2, uniform policy, seed {data['seed']}",
            "note acc",
            anchor="end",
            size=12.5,
        )
    )
    sd0, sd1 = series[0][2], series[1][2]
    return svg(
        W,
        H,
        "REINFORCE estimates with and without a baseline (measured in Lab 9)",
        f"Two histograms on the same horizontal axis, one above the other, of {K} one-batch REINFORCE estimates (batches of {N}) of one coordinate of the gradient at the uniform policy: the logit of the target's first symbol at step 1. Top, in gray: no baseline, standard deviation {sd0:.3f}. Bottom, in the accent color: the leave-one-out baseline, standard deviation {sd1:.3f}. A dashed vertical line across both marks the exact gradient, {exact:.4f}. Both histograms are centered near it; the bottom one is visibly narrower. The estimates are measured: Lab 9 writes them in Exercise 2.",
        b,
    )


def fig_reward_model() -> str:
    W, H = 760, 486
    yw, yx, yl = 84, 168, 252  # rows: preferred response, prompt, rejected response
    b: list[str] = []
    # inputs
    b.append(rect(28, yw - 20, 66, 40, "abox"))
    b.append(M(61, yw + 6, "y_w"))
    b.append(text(61, yw - 28, "preferred", "note acc"))
    # check mark on the preferred response
    b.append(
        f'<circle cx="94" cy="{yw - 20}" r="9" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.5"/>'
    )
    b.append(
        path(f"M89,{yw - 20} l3.5,4 l6,-7.5", cls="aln", mk=None, extra=' style="stroke-width:2"')
    )
    b.append(rect(28, yx - 20, 66, 40, "box"))
    b.append(M(61, yx + 6, "x"))
    b.append(text(61, yx + 38, "prompt", "note"))
    b.append(
        f'<rect x="28" y="{yl - 20}" width="66" height="40" rx="6" fill="{PALE}" stroke="{DIM}" stroke-width="1.5"/>'
    )
    b.append(M(61, yl + 6, "y_l", cls="note"))
    b.append(text(61, yl + 38, "rejected", "note"))
    # x joins each response
    jx = 160
    b.append(line(94, yx, jx, yx, mk=None))
    b.append(line(jx, yw + 10, jx, yl - 10, mk=None))
    b.append(line(94, yw, jx, yw, cls="aln", mk=None, extra=' style="stroke-width:1.5"'))
    b.append(line(94, yl, jx, yl, mk=None, extra=f' style="stroke:{DIM}"'))
    for y in (yw, yl):
        b.append(dot(jx, y, 4))
        b.append(path(f"M{jx},{y} V{y + (10 if y == yw else -10)}", mk=None))
    rx0, rw = 262, 86
    b.append(line(jx, yw, rx0 - 2, yw))
    b.append(line(jx, yl, rx0 - 2, yl))
    b.append(M((jx + rx0) / 2, yw - 9, "(x, y_w)", size=15))
    b.append(M((jx + rx0) / 2, yl - 9, "(x, y_l)", size=15))
    # two copies of one reward model
    for y in (yw, yl):
        b.append(rect(rx0, y - 22, rw, 44, "box"))
        b.append(M(rx0 + rw / 2, y + 7, "r_φ", size=21))
    mx = rx0 + rw / 2
    b.append(line(mx, yw + 22, mx, yl - 22, cls="dln", mk=None))
    b.append(text(mx + 10, yx - 3, "shared", "note", anchor="start"))
    b.append(M(mx + 10, yx + 15, "\\t{parameters }φ", size=14, anchor="start", cls="note"))
    # outputs meet at a minus sign
    cx, cy, cr = 498, yx, 14
    b.append(path(f"M{rx0 + rw},{yw} H{cx} V{cy - cr - 2}"))
    b.append(path(f"M{rx0 + rw},{yl} H{cx} V{cy + cr + 2}"))
    b.append(M(rx0 + rw + 10, yw - 9, "r_w = r_φ(x, y_w)", size=15, anchor="start"))
    b.append(M(rx0 + rw + 10, yl + 22, "r_l = r_φ(x, y_l)", size=15, anchor="start"))
    b.append(text(cx + 10, cy - cr - 8, "+", "b", anchor="start", size=15))
    b.append(text(cx + 10, cy + cr + 20, "−", "b", anchor="start", size=15))
    b.append(f'<circle class="op" cx="{cx}" cy="{cy}" r="{cr}"/>')
    b.append(line(cx - 6, cy, cx + 6, cy, mk=None))
    # sigma, the probability and the loss
    sx0 = 588
    b.append(line(cx + cr, cy, sx0 - 2, cy))
    b.append(M((cx + cr + sx0) / 2, cy - 9, "Δ", size=16))
    b.append(rect(sx0, cy - 18, 44, 36, "op", rx=6))
    b.append(M(sx0 + 22, cy + 6, "σ", size=19))
    px = sx0 + 22
    b.append(line(px, cy + 18, px, 222))
    b.append(M(px, 244, "P(y_w\\t{ preferred})", size=16))
    b.append(M(px, 266, "= σ(r_w − r_l)", size=16))
    b.append(line(px, 274, px, 296))
    b.append(rect(px - 98, 298, 196, 36, "abox"))
    b.append(M(px, 322, "\\t{loss} = −\\r{log} σ(r_w − r_l)", size=16))
    # inset: -log sigma(Delta) against Delta
    ix0, ix1, iy0, iy1 = 566, 736, 386, 446
    dmin, dmax, lmax = -4.0, 4.0, 4.2

    def IX(d: float) -> float:
        return ix0 + (d - dmin) / (dmax - dmin) * (ix1 - ix0)

    def IY(v: float) -> float:
        return iy1 - v / lmax * (iy1 - iy0)

    b.append(rect(ix0 - 52, iy0 - 28, ix1 - ix0 + 66, iy1 - iy0 + 64, "panel", rx=6))
    b.append(M(ix0 - 44, iy0 - 8, "−\\r{log} σ(Δ)", size=14, anchor="start"))
    b.append(line(ix0, iy1, ix1, iy1, mk=None, extra=f' style="stroke:{MUTED};stroke-width:1"'))
    b.append(line(IX(0), iy0, IX(0), iy1, cls="rule", mk=None, extra=' style="stroke-width:1"'))
    curve = [(IX(d), IY(math.log1p(math.exp(-d)))) for d in [dmin + i * 0.1 for i in range(81)]]
    b.append(path(poly(curve), cls="aln", mk=None, extra=' style="stroke-width:2"'))
    b.append(dot(IX(0), IY(math.log(2)), 3.6, NAVY))
    b.append(
        text(IX(0) + 8, IY(math.log(2)) - 7, "log 2 at Δ = 0", "note", anchor="start", size=12)
    )
    for d in (-4, 0, 4):
        b.append(text(IX(d), iy1 + 15, fmt_tick(d), "note", size=11.5))
    b.append(text((ix0 + ix1) / 2, iy1 + 28, "Δ", "note i", size=12))
    # legend
    b.append(
        M(28, 352, "Δ = r_w − r_l\\t{: the gap between the two scores.}", size=15, anchor="start")
    )
    b.append(text(28, 380, "Training lowers the loss by widening the gap:", "note", anchor="start"))
    b.append(
        text(28, 400, "the winner's score goes up, the loser's goes down.", "note", anchor="start")
    )
    b.append(
        text(28, 428, "Adding a constant to both scores changes nothing:", "note", anchor="start")
    )
    b.append(text(28, 448, "only their difference enters the loss.", "note", anchor="start"))
    return svg(
        W,
        H,
        "The reward model and its pairwise loss",
        "Left: a prompt box x, with the preferred response y_w above it (accent outline and a check mark) and the rejected response y_l below it (gray). The prompt joins each response, and each pair, (x, y_w) and (x, y_l), enters its own copy of one box r_phi; a dashed line between the two copies is labeled shared parameters phi. The two outputs, r_w = r_phi(x, y_w) and r_l = r_phi(x, y_l), meet at a circled minus sign, r_w with a plus and r_l with a minus. The difference Delta = r_w - r_l passes through a box sigma, giving P(y_w preferred) = sigma(r_w - r_l), and then the loss box: loss = -log sigma(r_w - r_l). An inset at the bottom right plots -log sigma(Delta) against Delta from -4 to 4: it falls toward 0 for large Delta, and the point at Delta = 0 is marked log 2.",
        b,
    )


# ==================================================================== Module 10


def person(x: float, y: float, color: str = NAVY) -> str:
    """A small person icon: head at (x, y)."""
    return (
        f'<circle cx="{f(x)}" cy="{f(y)}" r="6" fill="#ffffff" stroke="{color}" stroke-width="1.5"/>'
        f'<path d="M{f(x - 10)},{f(y + 22)} q0,-13 10,-13 q10,0 10,13" fill="#ffffff" stroke="{color}" stroke-width="1.5"/>'
    )


def lock(x: float, y: float) -> str:
    """A small padlock: body top-left at (x, y)."""
    return (
        f'<path d="M{f(x + 3)},{f(y)} v-4 a4,4 0 0 1 8,0 v4" fill="none" stroke="{MUTED}" stroke-width="1.5"/>'
        f'<rect x="{f(x)}" y="{f(y)}" width="14" height="10" rx="2" fill="{MUTED}"/>'
    )


def labeled_arrow(
    b: list[str], x: float, y0: float, y1: float, lines: list[str], ly: float, hw: float
) -> None:
    """A vertical arrow with a block of label lines on a patch of the panel color over it."""
    b.append(line(x, y0, x, y1 - 1))
    b.append(
        f'<rect x="{f(x - hw)}" y="{f(ly - 17)}" width="{f(2 * hw)}" height="{f(20 * len(lines) + 4)}" fill="#fafbfc"/>'
    )
    for i, s in enumerate(lines):
        b.append(M(x, ly + 20 * i, s, size=14, cls="note" if i else ""))


def fig_rlhf_pipeline() -> str:
    W, H = 800, 438
    P = [(16, 216), (256, 486), (526, 784)]  # panel x ranges
    pt, pb = 40, 372
    b: list[str] = []
    titles = ["1. Supervised fine-tuning", "2. Reward model", "3. Policy optimization"]
    for (xa, xb), title, tag in zip(P, titles, ["Lab 7", "Lab 9", "Lab 10"], strict=True):
        b.append(rect(xa, pt, xb - xa, pb - pt, "panel", rx=10))
        b.append(text((xa + xb) / 2, pt + 26, title, "b", size=15))
        b.append(rect((xa + xb) / 2 - 30, pb + 12, 60, 22, "op", rx=11))
        b.append(text((xa + xb) / 2, pb + 28, tag, "note", size=13))
    # panel 1
    c1 = (P[0][0] + P[0][1]) / 2
    b.append(rect(c1 - 62, 84, 124, 38, "box"))
    b.append(text(c1, 108, "pretrained LM", size=15))
    labeled_arrow(
        b,
        c1,
        122,
        290,
        ["\\t{demonstrations}", "\\t{(prompt, written response)}", "\\t{masked NLL (Module 7)}"],
        186,
        90,
    )
    b.append(rect(c1 - 40, 290, 80, 40, "abox"))
    b.append(M(c1, 317, "π_\\r{SFT}"))
    # panel 2
    c2 = (P[1][0] + P[1][1]) / 2
    b.append(rect(c2 - 40, 78, 80, 38, "abox"))
    b.append(M(c2, 104, "π_\\r{SFT}"))
    b.append(M(c2 + 50, 94, "\\t{one prompt }x\\t{,}", size=13.5, anchor="start", cls="note"))
    b.append(M(c2 + 50, 110, "K\\t{ samples}", size=13.5, anchor="start", cls="note"))
    chips = [(c2 - 84, "y_1"), (c2 - 34, "y_2"), (c2 + 16, "…"), (c2 + 66, "y_K")]
    for cx, lab in chips:
        b.append(
            line(
                c2,
                116,
                cx,
                140,
                mk="c" if lab != "…" else None,
                extra=f' style="stroke:{MUTED};stroke-width:1.2"',
            )
        )
        if lab == "…":
            b.append(text(cx, 160, "…", "note", size=16))
        else:
            b.append(rect(cx - 18, 142, 36, 26, "op", rx=4))
            b.append(M(cx, 161, lab, size=16))
    b.append(person(c2 - 78, 186))
    b.append(M(c2 + 10, 204, "y_2 ≻ y_K ≻ y_1", size=16))
    b.append(text(c2 + 10, 222, "a person ranks them", "note", size=12.5))
    labeled_arrow(
        b,
        c2,
        232,
        312,
        ["\\t{pairs }(x, y_w, y_l)", "\\t{Bradley–Terry loss (Module 9)}"],
        264,
        104,
    )
    b.append(rect(c2 - 74, 312, 148, 40, "abox"))
    b.append(M(c2, 338, "r_φ(x, y) → \\t{scalar}", size=17))
    # panel 3
    xa3 = P[2][0]
    ty = 196  # the policy row
    pix, rfx = xa3 + 46, xa3 + 186  # left edges of pi_theta and r_phi
    b.append(rect(pix, 78, 60, 38, "dim"))
    b.append(M(pix + 30, 103, "π_\\r{ref}", size=18))
    b.append(lock(pix + 66, 90))
    b.append(text(pix + 86, 92, "frozen copy", "note", anchor="start", size=12.5))
    b.append(M(pix + 86, 108, "\\t{of }π_\\r{SFT}", size=13.5, anchor="start", cls="note"))
    b.append(line(pix + 30, 116, pix + 30, ty - 20, cls="dln", mk=None))
    b.append(text(pix + 40, 146, "KL penalty,", "note", anchor="start", size=12.5))
    b.append(M(pix + 40, 163, "β", size=15, anchor="start", cls="note"))
    b.append(M(xa3 + 22, ty + 6, "x", size=19))
    b.append(line(xa3 + 32, ty, pix - 2, ty))
    b.append(rect(pix, ty - 20, 60, 40, "box"))
    b.append(M(pix + 30, ty + 6, "π_θ"))
    b.append(line(pix + 60, ty, rfx - 2, ty))
    b.append(M((pix + 60 + rfx) / 2, ty - 8, "\\t{sample }y", size=13.5, cls="note"))
    b.append(rect(rfx, ty - 20, 48, 40, "abox"))
    b.append(M(rfx + 24, ty + 6, "r_φ"))
    b.append(M(rfx + 24, ty - 28, "\\t{scores }y", size=13.5, cls="note"))
    b.append(path(f"M{rfx + 24},{ty + 20} V{ty + 54} H{pix + 30} V{ty + 22}"))
    b.append(
        M((pix + rfx + 54) / 2, ty + 74, "\\t{policy-gradient update of }θ", size=13.5, cls="note")
    )
    b.append(text((P[2][0] + P[2][1]) / 2, ty + 112, "PPO in practice;", "note", size=12))
    b.append(text((P[2][0] + P[2][1]) / 2, ty + 128, "REINFORCE in the lab", "note", size=12))
    # arrows between the panels
    for (xa, _), (_, xb), lab in [(P[1], P[0], "π_\\r{SFT}"), (P[2], P[1], "r_φ")]:
        b.append(line(xb + 4, 210, xa - 4, 210, cls="aln", mk="b"))
        b.append(M((xa + xb) / 2, 200, lab, size=16, cls="acc"))
    return svg(
        W,
        H,
        "The three stages of RLHF",
        "Three panels from left to right, joined by arrows. Panel 1, supervised fine-tuning (Lab 7): a pretrained LM, trained on demonstrations (prompt, written response) with the masked NLL of Module 7, gives pi_SFT. An arrow carries pi_SFT to panel 2, the reward model (Lab 9): pi_SFT samples K responses y_1 to y_K for one prompt x, a person ranks them, and pairs (x, y_w, y_l) train r_phi(x, y), which returns a scalar, with the Bradley-Terry loss of Module 9. An arrow carries r_phi to panel 3, policy optimization (Lab 10): a loop in which the prompt x goes to pi_theta, a sampled response y goes to r_phi, which scores it, and a policy-gradient update changes theta. Above pi_theta, a frozen reference pi_ref, a copy of pi_SFT drawn with a dashed outline and a lock, is joined to pi_theta by a dashed line labeled KL penalty, beta. Small type: PPO in practice; REINFORCE in the lab.",
        b,
    )


def fig_reward_drift() -> str:
    W, H = 700, 420
    x0, x1, y0, y1 = 84, 640, 52, 316  # plot area: left, right, top, bottom

    def proxy(t: float) -> float:  # rises monotonically and flattens slowly
        return 0.95 * (1 - math.exp(-3 * t)) + 0.25 * t

    def gold(t: float) -> float:  # rises with the proxy, peaks at t = 0.4, then falls
        return 2.6 * t * math.exp(-2.5 * t)

    peak, big_beta, beta0 = 0.4, 0.2, 0.96
    vmax = 1.3

    def P(t: float, v: float) -> tuple[float, float]:
        return x0 + t * (x1 - x0), y1 - v / vmax * (y1 - y0)

    ts = [i / 200 for i in range(201)]
    b: list[str] = []
    # axes, with arrowheads and no numbers
    b.append(line(x0, y1, x1 + 18, y1, mk="c", extra=f' style="stroke:{MUTED}"'))
    b.append(line(x0, y1, x0, y0 - 18, mk="c", extra=f' style="stroke:{MUTED}"'))
    b.append(vtext(x0 - 20, (y0 + y1) / 2, "reward", "note"))
    b.append(text(x0 - 8, y1 + 5, "0", "note", anchor="end", size=12))
    # where training stops
    for t, lab in [(big_beta, "\\t{large }β\\t{ stops here}"), (beta0, "β = 0\\t{ ends here}")]:
        px, _ = P(t, 0)
        b.append(
            line(px, y1, px, P(t, proxy(t))[1], cls="dln", mk=None, extra=' style="stroke-width:1"')
        )
        b.append(
            f'<path d="M{px:.1f},{y1 - 1} l-7,13 h14 z" fill="{mix(MUTED, "#ffffff", 0.35)}" stroke="{MUTED}" stroke-width="1"/>'
        )
        b.append(M(px, y1 + 32, lab, size=14, cls="note"))
    # over-optimization
    px, py = P(peak, gold(peak))
    b.append(
        line(
            px,
            y1,
            px,
            y0 + 6,
            mk=None,
            extra=f' style="stroke:{INK};stroke-width:1.2;stroke-dasharray:6 4"',
        )
    )
    b.append(
        text(px - 8, y0 + 14, "over-optimization starts here", "note b", anchor="end", size=13.5)
    )
    b.append(dot(px, py, 4, NAVY))
    # the curves
    b.append(path(poly([P(t, proxy(t)) for t in ts]), cls="aln", mk=None))
    b.append(
        path(
            poly([P(t, gold(t)) for t in ts]),
            mk=None,
            extra=f' style="stroke:{NAVY};stroke-width:2.5"',
        )
    )
    lx, ly = P(1, proxy(1))
    b.append(text(lx - 4, ly - 26, "reward-model score (proxy)", "acc b", anchor="end", size=14))
    b.append(text(lx - 4, ly - 10, "keeps rising", "note", anchor="end", size=12.5))
    gx, gy = P(1, gold(1))
    b.append(text(gx - 4, gy + 24, "gold reward", "b", anchor="end", size=14))
    b.append(text(gx - 4, gy + 40, "rises, peaks, then falls", "note", anchor="end", size=12.5))
    b.append(
        text((x0 + x1) / 2, y1 + 64, "drift from the reference, KL (nats per response)", size=14)
    )
    b.append(
        text(
            W - 16,
            H - 12,
            "schematic: the shape reported by Gao et al. (2023); no measured values",
            "note",
            anchor="end",
            size=12,
        )
    )
    return svg(
        W,
        H,
        "Reward over-optimization (schematic)",
        "A schematic plot with no numbers on the axes. The horizontal axis is the drift from the reference policy, KL in nats per response, starting at 0; the vertical axis is reward. Two curves start at the origin. The reward-model score, the proxy, rises steadily and flattens slowly. The gold reward rises with it at first, peaks, and then falls while the proxy keeps rising. A dashed vertical line at the gold peak is labeled over-optimization starts here. Two markers on the horizontal axis: large beta stops here, left of the peak, and beta = 0 ends here, far to the right, where the gold reward has fallen.",
        b,
    )


# ==================================================================== Module 11


def measure_calibration() -> None:
    """Rerun Lab 11's Lab 1 classifier path and write images/11-calibration.json."""
    import csv
    import gzip

    import numpy as np
    import scipy
    import sklearn
    from scipy.optimize import minimize_scalar
    from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
    from sklearn.linear_model import LogisticRegression

    splits = {"train": ([], []), "val": ([], []), "test": ([], [])}
    with gzip.open(ROOT / "data" / "arxiv_topics_v1.csv.gz", "rt", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            texts, labels = splits[row["split"]]
            texts.append(row["title"] + "\n" + row["abstract"])
            labels.append(int(row["label"]))

    def tokenize(s: str) -> list[str]:  # Lab 1's tokenizer, as Lab 11 restates it
        return re.findall(r"[a-z0-9']+|[^a-z0-9'\s]", s.lower())

    (tr_x, y_tr), (va_x, y_va), (te_x, y_te) = (splits[s] for s in ("train", "val", "test"))
    y_tr, y_va, y_te = (np.array(y) for y in (y_tr, y_va, y_te))
    vectorizer = CountVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None, min_df=2)
    tfidf = TfidfTransformer()
    X_tr = tfidf.fit_transform(vectorizer.fit_transform(tr_x))
    X_va = tfidf.transform(vectorizer.transform(va_x))
    X_te = tfidf.transform(vectorizer.transform(te_x))

    def log_softmax(z):
        z = z - z.max(axis=1, keepdims=True)
        return z - np.log(np.exp(z).sum(axis=1, keepdims=True))

    def fit_temperature(val_logits, val_labels) -> float:  # Lab 11, Solution 3
        rows = np.arange(len(val_labels))

        def val_nll(log_tau):
            return -log_softmax(val_logits / np.exp(log_tau))[rows, val_labels].mean()

        return float(np.exp(minimize_scalar(val_nll, bounds=(-3, 3), method="bounded").x))

    def reliability_bins(conf, correct, n_bins=15):  # Lab 11, Solution 1 (equal width)
        edges = np.linspace(0, 1, n_bins + 1)
        bins = np.digitize(conf, edges[1:-1], right=True)
        counts = np.bincount(bins, minlength=n_bins)
        with np.errstate(invalid="ignore", divide="ignore"):
            mean_conf = np.bincount(bins, weights=conf, minlength=n_bins) / counts
            acc = np.bincount(bins, weights=correct, minlength=n_bins) / counts
        full = counts > 0
        ece = float(np.sum(counts[full] / counts.sum() * np.abs(acc[full] - mean_conf[full])))
        return {
            "counts": counts.tolist(),
            "mean_conf": [
                round(float(v), 5) if c else None for v, c in zip(mean_conf, counts, strict=True)
            ],
            "acc": [round(float(v), 5) if c else None for v, c in zip(acc, counts, strict=True)],
            "ece": round(ece, 5),
            "accuracy": round(float(correct.mean()), 5),
        }

    def outcomes(logits, labels, tau=1.0):
        p = np.exp(log_softmax(logits / tau))
        return p.max(axis=1), (p.argmax(axis=1) == labels).astype(np.float64)

    fits = {}
    for C in (1.0, 10.0):
        model = LogisticRegression(C=C, max_iter=1000, random_state=0).fit(X_tr, y_tr)
        fits[C] = (model.decision_function(X_va), model.decision_function(X_te))
    val1, test1 = fits[1.0]
    tau = fit_temperature(val1, y_va)
    conf10, correct10 = outcomes(fits[10.0][1], y_te)
    order = np.argsort(-conf10, kind="stable")
    data = {
        "description": "Lab 1 classifier (TF-IDF + logistic regression) on the 1,600 arXiv Topics v1 test papers, recomputed with Lab 11's code for the Module 11 figures images/11-reliability.svg and images/11-risk-coverage.svg.",
        "how": "uv run --group execute python scripts/make_figures_09_11.py --measure",
        "packages": {
            "scikit-learn": sklearn.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "features": int(X_tr.shape[1]),
        "reliability": {
            "C": 1,
            "n_bins": 15,
            "N": len(y_te),
            "tau_star": round(tau, 4),
            "tau_fitted_on": "val (600 papers)",
            "before": reliability_bins(*outcomes(test1, y_te)),
            "after": reliability_bins(*outcomes(test1, y_te, tau)),
        },
        "risk_coverage": {
            "C": 10,
            "N": len(y_te),
            "confidence_desc": [round(float(v), 6) for v in conf10[order]],
            "correct_desc": "".join(str(int(v)) for v in correct10[order]),
        },
    }
    out = json.dumps(data, indent=1)
    out = re.sub(
        r"\[\s+([^\[\]{}]*?)\s+\]", lambda m: "[" + " ".join(m.group(1).split()) + "]", out
    )
    CALIBRATION.write_text(out + "\n", encoding="utf-8")
    rel = data["reliability"]
    print(
        f"wrote {CALIBRATION.relative_to(ROOT)}: C = 1 ECE {rel['before']['ece']:.4f} -> "
        f"{rel['after']['ece']:.4f} at tau* {rel['tau_star']:.3f}; C = 10 accuracy {correct10.mean():.4f}"
    )


def load_calibration() -> dict:
    data = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    rel = data["reliability"]
    for key in ("before", "after"):
        s = rel[key]
        n = sum(s["counts"])
        ece = sum(
            c / n * abs(a - m)
            for c, a, m in zip(s["counts"], s["acc"], s["mean_conf"], strict=True)
            if c
        )
        assert n == rel["N"] and abs(ece - s["ece"]) < 1e-4, "bins must reproduce the ECE"
    # The module quotes these values (section 3, section 6 and Figure 11.1's titles).
    assert round(rel["before"]["ece"], 3) == 0.164 and round(rel["after"]["ece"], 3) == 0.009
    assert round(rel["tau_star"], 2) == 0.47
    return data


def axes(
    b: list[str],
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    xticks: list[float],
    yticks: list[float],
    X,
    Y,
    grid: bool = True,
    size: float = 12,
) -> None:
    """Gridlines, a frame on the left and bottom, and tick labels."""
    for v in yticks:
        if grid:
            b.append(line(x0, Y(v), x1, Y(v), cls="rule", mk=None, extra=' style="stroke-width:1"'))
        b.append(text(x0 - 7, Y(v) + 4, fmt_tick(v), "note", anchor="end", size=size))
    for v in xticks:
        if grid:
            b.append(line(X(v), y0, X(v), y1, cls="rule", mk=None, extra=' style="stroke-width:1"'))
        b.append(text(X(v), y1 + 16, fmt_tick(v), "note", size=size))
    b.append(
        path(f"M{x0},{y0} V{y1} H{x1}", mk=None, extra=f' style="stroke:{MUTED};stroke-width:1"')
    )


def fig_reliability() -> str:
    data = load_calibration()
    rel = data["reliability"]
    N, nb = rel["N"], rel["n_bins"]
    W, H = 780, 566
    side, top = 270, 64  # plot side and top
    hist_top, hist_h = top + side + 54, 74
    lefts = [76, 470]
    hmax = 1000
    assert max(max(rel[k]["counts"]) for k in ("before", "after")) <= hmax
    b: list[str] = []
    titles = [
        f'<text x="{{x}}" y="{{y}}" text-anchor="middle" style="font-size:15px" class="b"><tspan class="mono">C</tspan> = 1: ECE {rel["before"]["ece"]:.3f}</text>',
        None,
    ]
    for k, (key, x0) in enumerate(zip(("before", "after"), lefts, strict=True)):
        s = rel[key]
        x1, y0, y1 = x0 + side, top, top + side

        def X(v: float, x0=x0) -> float:
            return x0 + v * side

        def Y(v: float, y1=y1) -> float:
            return y1 - v * side

        ticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        axes(b, x0, x1, y0, y1, ticks, ticks, X, Y)
        b.append(
            line(
                X(0),
                Y(0),
                X(1),
                Y(1),
                mk=None,
                extra=f' style="stroke:{MUTED};stroke-width:1.2;stroke-dasharray:5 4"',
            )
        )
        b.append(
            f'<text transform="translate({X(0.06):.1f},{Y(0.06) + 18:.1f}) rotate(-45)" text-anchor="start" class="note" style="font-size:12px">perfect calibration</text>'
        )
        for c, m, a in zip(s["counts"], s["mean_conf"], s["acc"], strict=True):
            if c:
                b.append(
                    line(
                        X(m),
                        Y(m),
                        X(m),
                        Y(a),
                        mk=None,
                        extra=f' style="stroke:{ACCENT};stroke-width:4;stroke-opacity:0.55"',
                    )
                )
        for c, m, a in zip(s["counts"], s["mean_conf"], s["acc"], strict=True):
            if c:
                r = 2 + 0.3 * math.sqrt(c)
                b.append(
                    f'<circle cx="{X(m):.1f}" cy="{Y(a):.1f}" r="{r:.1f}" fill="{NAVY}" fill-opacity="0.85" stroke="#ffffff" stroke-width="1"/>'
                )
        b.append(text((x0 + x1) / 2, y1 + 34, "confidence (mean per bin)", "note", size=13))
        if k == 0:
            b.append(titles[0].format(x=f((x0 + x1) / 2), y=top - 16))
            b.append(vtext(x0 - 40, (y0 + y1) / 2, "accuracy (mean per bin)"))
            b.append(
                text(X(0.04), Y(0.9), "above the diagonal:", "note", anchor="start", size=12.5)
            )
            b.append(
                text(X(0.04), Y(0.9) + 16, "underconfident", "note b", anchor="start", size=12.5)
            )
            b.append(
                text(X(0.96), Y(0.12), "below: overconfident", "note", anchor="end", size=12.5)
            )
        else:
            b.append(
                M(
                    (x0 + x1) / 2,
                    top - 16,
                    f"\\t{{after temperature scaling (}}τ\\t{{ = {rel['tau_star']:.2f}): ECE {s['ece']:.3f}}}",
                    size=15,
                    cls="b",
                )
            )
        # histogram of the test confidences: the bin counts
        hb = hist_top + hist_h
        for v in (0, 500, 1000):
            yy = hb - hist_h * v / hmax
            b.append(line(x0, yy, x1, yy, cls="rule", mk=None, extra=' style="stroke-width:1"'))
            b.append(text(x0 - 7, yy + 4, f"{v:,}", "note", anchor="end", size=11.5))
        for i, c in enumerate(s["counts"]):
            if c:
                hgt = hist_h * c / hmax
                b.append(
                    f'<rect x="{X(i / nb) + 1:.1f}" y="{hb - hgt:.1f}" width="{side / nb - 2:.1f}" height="{hgt:.1f}" fill="{mix(NAVY, "#ffffff", 0.45)}"/>'
                )
        b.append(
            path(
                f"M{x0},{hist_top} V{hb} H{x1}",
                mk=None,
                extra=f' style="stroke:{MUTED};stroke-width:1"',
            )
        )
        for v in (0, 0.5, 1.0):
            b.append(text(X(v), hb + 15, fmt_tick(v), "note", size=11.5))
        if k == 0:
            b.append(vtext(x0 - 46, hist_top + hist_h / 2, "papers"))
        b.append(
            text(
                x0 + 6,
                hist_top + 12,
                f"histogram of the {N:,} test confidences",
                "note",
                anchor="start",
                size=12,
            )
        )
    # legend
    ly = H - 40
    b.append(f'<circle cx="84" cy="{ly - 4}" r="6" fill="{NAVY}" fill-opacity="0.85"/>')
    b.append(text(96, ly, "one bin: area grows with its count", "note", anchor="start", size=12.5))
    b.append(
        line(
            320,
            ly - 11,
            320,
            ly + 3,
            mk=None,
            extra=f' style="stroke:{ACCENT};stroke-width:4;stroke-opacity:0.55"',
        )
    )
    b.append(text(330, ly, "gap to the diagonal", "note", anchor="start", size=12.5))
    b.append(
        text(
            W - 16,
            H - 14,
            f"measured: Lab 1 classifier, {N:,} test papers, {nb} bins; τ fitted on the validation set",
            "note acc",
            anchor="end",
            size=12.5,
        )
    )
    bf, af = rel["before"], rel["after"]
    return svg(
        W,
        H,
        "Reliability diagrams of the Lab 1 classifier before and after temperature scaling (measured)",
        f"Two reliability diagrams side by side, confidence (mean per bin) against accuracy (mean per bin), both from 0 to 1, with a dashed diagonal labeled perfect calibration. Each non-empty bin of {nb} is a dot whose area grows with its count, joined to the diagonal by a shaded bar. Left, the Lab 1 classifier with C = 1, ECE {bf['ece']:.3f}: the dots lie well above the diagonal, the model is right more often than its confidence says (underconfident); its confidences spread from about 0.3 to 1. Right, the same model after temperature scaling with tau = {rel['tau_star']:.2f}, ECE {af['ece']:.3f}: the dots lie on the diagonal, and most confidences have moved up, {af['counts'][-1]} of the {N} into the top bin. Under each diagram, a histogram of the {N} test confidences.",
        b,
    )


def risk_curve(conf: list[float], correct: str) -> tuple[list[float], list[float]]:
    """Lab 11's risk_coverage on confidences sorted from the highest down: one step per value."""
    n = len(conf)
    cov, risk, errors = [], [], 0
    for i, (c, o) in enumerate(zip(conf, correct, strict=True)):
        errors += o == "0"
        if i == n - 1 or conf[i + 1] != c:
            cov.append((i + 1) / n)
            risk.append(errors / (i + 1))
    return cov, risk


def fig_risk_coverage() -> str:
    rc = load_calibration()["risk_coverage"]
    conf, correct, N = rc["confidence_desc"], rc["correct_desc"], rc["N"]
    assert len(conf) == len(correct) == N and conf == sorted(conf, reverse=True)
    cov, risk = risk_curve(conf, correct)
    err = risk[-1]
    acc = 1 - err
    lam, l_wrong, l_defer = 0.9, 10, 1
    assert lam == 1 - l_defer / l_wrong  # Chow's rule
    acted = sum(c >= lam for c in conf)
    c_star, r_star = acted / N, correct[:acted].count("0") / acted
    # The module quotes these (section 8, the measured worked example).
    assert round(err, 3) == 0.116 and round(c_star, 3) == 0.578 and round(r_star, 3) == 0.022
    W, H = 700, 430
    x0, x1, y0, y1 = 86, 660, 40, 344
    rmax = 0.14

    def X(v: float) -> float:
        return x0 + v * (x1 - x0)

    def Y(v: float) -> float:
        return y1 - v / rmax * (y1 - y0)

    b: list[str] = []
    axes(
        b,
        x0,
        x1,
        y0,
        y1,
        [0, 0.2, 0.4, 0.6, 0.8, 1.0],
        [0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14],
        X,
        Y,
    )
    b.append(text((x0 + x1) / 2, y1 + 40, "coverage (share of cases acted on)", size=14))
    b.append(vtext(26, (y0 + y1) / 2, "selective risk (error rate among them)", "note"))
    # random abstention and the oracle
    b.append(
        line(
            X(0),
            Y(err),
            X(1),
            Y(err),
            mk=None,
            extra=f' style="stroke:{MUTED};stroke-width:2;stroke-dasharray:1.5 4;stroke-linecap:round"',
        )
    )
    b.append(
        text(
            X(0.02),
            Y(err) - 8,
            f"random abstention: {err:.3f} at every coverage",
            "note",
            anchor="start",
            size=13,
        )
    )
    oracle = [(X(0), Y(0)), (X(acc), Y(0))] + [
        (X(c), Y((c - acc) / c)) for c in [acc + (1 - acc) * i / 20 for i in range(1, 21)]
    ]
    b.append(
        path(
            poly(oracle),
            mk=None,
            extra=f' style="stroke:{INK};stroke-width:1.8;stroke-dasharray:7 4"',
        )
    )
    b.append(
        text(
            X(acc) - 4,
            Y(0) - 7,
            f"oracle (dashed): defers the {err:.1%} it gets wrong first",
            "note",
            anchor="end",
            size=12,
        )
    )
    # the measured curve
    pts = [(X(c), Y(r)) for c, r in zip(cov, risk, strict=True)]
    b.append(
        path(
            poly([(X(0), Y(0))] + pts),
            mk=None,
            extra=f' style="stroke:{NAVY};stroke-width:2.2;stroke-linejoin:round"',
        )
    )
    b.append(text(X(0.83), Y(0.076), "Lab 1 classifier, C = 10", "b", anchor="end", size=14))
    b.append(
        text(X(0.83), Y(0.076) + 17, "measured on the test set", "note", anchor="end", size=12.5)
    )
    # Chow's threshold
    px, py = X(c_star), Y(r_star)
    b.append(dot(px, py, 6, ACCENT))
    b.append(
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="none" stroke="#ffffff" stroke-width="1.5"/>'
    )
    b.append(
        path(
            f"M{px - 5:.1f},{py - 6:.1f} L{X(0.46):.1f},{Y(0.056):.1f}",
            mk=None,
            extra=f' style="stroke:{ACCENT};stroke-width:1"',
        )
    )
    b.append(
        M(
            X(0.18),
            Y(0.056) - 26,
            "λ^* = 0.9 (ℓ_\\t{wrong} = 10, ℓ_\\t{defer} = 1)",
            size=15,
            cls="acc",
            anchor="start",
        )
    )
    b.append(
        text(
            X(0.18),
            Y(0.056) - 6,
            f"Chow's rule: coverage {c_star:.3f}, risk {r_star:.3f}",
            "note",
            anchor="start",
            size=12.5,
        )
    )
    b.append(
        text(W - 16, H - 12, f"measured: {N:,} test papers", "note acc", anchor="end", size=12)
    )
    return svg(
        W,
        H,
        "Risk-coverage curve of the Lab 1 classifier (measured)",
        f"A plot of selective risk, the error rate among the cases acted on, from 0 to 0.14, against coverage, the share of cases acted on, from 0 to 1. The measured curve of the Lab 1 classifier with C = 10 is 0 up to a coverage of about {cov[[r > 0 for r in risk].index(True)]:.2f}, then rises, slowly at first and faster near full coverage, to the plain error rate {err:.3f} at coverage 1. A dotted horizontal line at {err:.3f} is random abstention. A dashed oracle curve is 0 up to coverage {acc:.3f} and then rises almost linearly to {err:.3f} at coverage 1. The model's curve lies between the two. A dot marks Chow's threshold lambda* = 0.9, for l_wrong = 10 and l_defer = 1: coverage {c_star:.3f}, risk {r_star:.3f}.",
        b,
    )


def check_captions() -> None:
    """Fail if a module caption quotes a measured number that the data do not give."""
    var = json.loads((IMAGES / "09-baseline-variance.json").read_text(encoding="utf-8"))["std"]
    cal = load_calibration()
    rel, rc = cal["reliability"], cal["risk_coverage"]
    _, risk = risk_curve(rc["confidence_desc"], rc["correct_desc"])
    acted = sum(c >= 0.9 for c in rc["confidence_desc"])
    chow = (acted / rc["N"], rc["correct_desc"][:acted].count("0") / acted)
    after = rel["after"]["counts"]
    low = [c for c in after if c][:2]
    expected = {
        ("09-preference-learning.qmd", "fig-baseline-variance"): [
            f"from {var['no_baseline']:.3f} to {var['leave_one_out']:.3f}"
        ],
        ("11-calibration.qmd", "fig-reliability"): [
            f"ECE {rel['before']['ece']:.3f}",
            f"ECE {rel['after']['ece']:.3f}",
            f"\\tau^* = {rel['tau_star']:.2f}",
            f"{after[-1]} of the {rel['N']:,}",
            f"hold {low[0]} and {low[1]} papers",
        ],
        ("11-calibration.qmd", "fig-risk-coverage"): [
            f"error rate, {risk[-1]:.3f}",
            f"coverage {chow[0]:.3f}, risk {chow[1]:.3f}",
        ],
    }
    for (page, fid), quotes in expected.items():
        caption = next(
            ln
            for ln in (ROOT / "modules" / page).read_text(encoding="utf-8").splitlines()
            if f"{{#{fid} " in ln
        )
        for q in quotes:
            assert q in caption, f"modules/{page} #{fid}: the caption should quote {q!r}"


FIGURES = {
    "09-text-as-mdp.svg": fig_text_as_mdp,
    "09-baseline-variance.svg": fig_baseline_variance,
    "09-reward-model.svg": fig_reward_model,
    "10-rlhf-pipeline.svg": fig_rlhf_pipeline,
    "10-reward-drift.svg": fig_reward_drift,
    "11-reliability.svg": fig_reliability,
    "11-risk-coverage.svg": fig_risk_coverage,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--measure",
        action="store_true",
        help="first recompute images/11-calibration.json (needs NumPy, SciPy, scikit-learn)",
    )
    if parser.parse_args().measure:
        measure_calibration()
    for name, fn in FIGURES.items():
        (IMAGES / name).write_text(fn(), encoding="utf-8")
        print(f"wrote images/{name}")
    check_captions()
    print("captions of Modules 9 and 11 quote the measured values")


if __name__ == "__main__":
    main()
