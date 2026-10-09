"""Write the system figures of Modules 12-15 as hand-laid-out SVG.

  images/12-act-ask-escalate.svg     expected cost of act, ask and escalate (Module 12, section 3)
  images/12-route-guard-verify.svg   a decision model as router, guard and verifier (section 4)
  images/13-rag-pipeline.svg         the RAG pipeline: indexing once, then per query (Module 13, section 2)
  images/13-bi-vs-cross-encoder.svg  bi-encoder retrieval against cross-encoder reranking (section 6)
  images/14-desk-agent-graph.svg     the desk agent as a LangGraph graph (Module 14, section 4)
  images/15-capstone-graph.svg       the capstone starter system as a graph (Module 15, section 2)

12-act-ask-escalate.svg is computed, not measured: the three lines are
eq-three-costs with the costs of Module 12's worked example, and the script
checks that their crossings are the thresholds the page states (0.375, 0.969
and Chow's 0.85) before it draws anything. The other five are schematics. The
node names, edge conditions and thresholds of the two graphs follow the
node tables of Modules 14 and 15 and the graph-building code of Labs 14 and 15
(build_graph in each notebook). An "Ex. N" tag marks a part that the lab's
Exercise N writes; tags appear only where the notebook confirms it.

The decision model is drawn generically: a box that returns a probability p
compared with thresholds. Nothing here shows how Jev or RLCD works (TypeSafe
has not published it); Choice and Noul are the names of Jev's public question
types, as the pages use them.

The style block, palette, markers and drawing helpers are imported from
make_figures_05_08.py, so the two scripts stay alike. Output is deterministic:
running the script twice gives identical files.

Run:  python scripts/make_figures_12_15.py      (standard library only)
"""

# SVG markup and the alt-text strings are kept on one line each, so they read as
# they appear in the output.
# ruff: noqa: E501

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from xml.sax.saxutils import escape

from make_figures_05_08 import (
    ACCENT,
    IMAGES,
    INK,
    MUTED,
    NAVY,
    M,
    dot,
    f,
    line,
    path,
    rect,
    svg,
    text,
)

# Decision models get one color in every figure, language models another (ACCENT).
PURPLE, PURPLE_FILL = "#6a4c9c", "#ece6f5"

EXTRA_STYLE = f"""<style>
    .dbox {{ fill: {PURPLE_FILL}; stroke: {PURPLE}; stroke-width: 1.5; }}
    .cln {{ fill: none; stroke: {NAVY}; stroke-width: 1.5; stroke-dasharray: 6 4; }}
    .dotted {{ fill: none; stroke: {MUTED}; stroke-width: 1.6; stroke-dasharray: 1.5 3.5; stroke-linecap: round; }}
    .bound {{ fill: none; stroke: {MUTED}; stroke-width: 1.4; stroke-dasharray: 2 4; stroke-linecap: round; }}
    .halo {{ paint-order: stroke; stroke: #ffffff; stroke-width: 5px; stroke-linejoin: round; }}
    .pill {{ fill: {NAVY}; }}
    .pilltext {{ fill: #ffffff; font-size: 12.5px; font-weight: 700; letter-spacing: 0.06em; }}
    .tagbox {{ fill: #ffffff; stroke: {MUTED}; stroke-width: 1; }}
    .tag {{ font-size: 12px; font-weight: 600; fill: {MUTED}; }}
    .sm {{ font-size: 13px; }}
    .m {{ font-variant-numeric: lining-nums; }}
  </style>"""


def figure(w: int, h: int, title: str, desc: str, body: list[str]) -> str:
    return svg(w, h, title, desc, body, [EXTRA_STYLE])


# ------------------------------------------------------------------ helpers


def rich(x, y, parts, cls="", size=None, anchor="middle") -> str:
    """One line of text from (string, class) parts, e.g. a code name inside a sentence."""
    st = f' style="font-size:{size}px"' if size else ""
    c = f' class="{cls}"' if cls else ""
    inner = "".join(
        f'<tspan class="{pc}">{escape(s)}</tspan>' if pc else escape(s) for s, pc in parts
    )
    return f'<text x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{c}{st}>{inner}</text>'


def node(b, x, y, w, h, cls, name, sub=None, mono=False, rx=8, size=15, math=False) -> None:
    """A box with a bold name and an optional note line under it (math=True: typeset with M)."""
    b.append(rect(x, y, w, h, cls, rx=rx))
    cx, name_cls = x + w / 2, "b mono" if mono else "b"
    if sub is None:
        b.append(text(cx, y + h / 2 + 5, name, name_cls, size=size))
        return
    b.append(text(cx, y + h / 2 - 3, name, name_cls, size=size))
    if math:
        b.append(M(cx, y + h / 2 + 15, sub, size=14, cls="note"))
    else:
        b.append(text(cx, y + h / 2 + 15, sub, "note sm"))


def pill(b, cx, cy, s) -> None:
    """START or END."""
    w = 18 + 9 * len(s)
    b.append(rect(cx - w / 2, cy - 13, w, 26, "pill", rx=13))
    b.append(text(cx, cy + 4.5, s, "pilltext"))


def tag(b, x_right, y_mid, s) -> None:
    """A small 'Ex. N' chip, right-aligned at x_right and centered on y_mid."""
    w = 12 + 6.6 * len(s)
    b.append(rect(x_right - w, y_mid - 9, w, 18, "tagbox", rx=9))
    b.append(text(x_right - w / 2, y_mid + 4.2, s, "tag"))


def gauge(b, x, y, w, p, ticks, plabel="p") -> None:
    """A probability gauge: a 0-to-1 track filled up to p, with threshold ticks under it."""
    b.append(
        f'<rect x="{f(x)}" y="{f(y - 3)}" width="{f(w)}" height="6" rx="3" fill="#ffffff" stroke="{PURPLE}" stroke-width="1.2"/>'
    )
    b.append(
        f'<rect x="{f(x)}" y="{f(y - 3)}" width="{f(w * p)}" height="6" rx="3" fill="{PURPLE}" fill-opacity="0.55"/>'
    )
    px = x + w * p
    b.append(
        f'<path d="M{f(px - 5)},{f(y - 13)} H{f(px + 5)} L{f(px)},{f(y - 5)} z" fill="{PURPLE}"/>'
    )
    b.append(M(px, y - 17, plabel, size=14))
    for v, lab in ticks:
        tx = x + w * v
        b.append(
            f'<line x1="{f(tx)}" y1="{f(y - 6)}" x2="{f(tx)}" y2="{f(y + 8)}" stroke="{INK}" stroke-width="1.6"/>'
        )
        b.append(M(tx, y + 23, lab, size=13.5))


def decision(b, x, y, w, name, kind, question, p, ticks, plabel="p", mono=False) -> None:
    """A decision-model box: name, question type, the question, and a gauge (height 118)."""
    b.append(rect(x, y, w, 118, "dbox", rx=10))
    cx = x + w / 2
    b.append(text(cx, y + 22, name, "b mono" if mono else "b", size=15))
    b.append(rich(cx, y + 40, [("decision model · ", ""), (kind, "mono")], "note sm"))
    b.append(text(cx, y + 57, question, "note sm i"))
    gauge(b, x + 22, y + 90, w - 44, p, ticks, plabel)


def pause_icon(b, x, y) -> None:
    b.append(f'<rect x="{f(x)}" y="{f(y)}" width="4" height="13" rx="1" fill="{INK}"/>')
    b.append(f'<rect x="{f(x + 7)}" y="{f(y)}" width="4" height="13" rx="1" fill="{INK}"/>')


def legend(b, x, y, items) -> None:
    """Legend rows: ("line", cls, label), ("box", cls, label), ("tag", s, label), ("pause", None, label)."""
    for k, (kind, arg, lab) in enumerate(items):
        yy = y + 22 * k
        if kind == "line":
            b.append(line(x, yy - 4, x + 34, yy - 4, cls=arg, mk="a" if arg != "dotted" else "c"))
        elif kind == "box":
            b.append(rect(x + 4, yy - 12, 26, 15, arg, rx=4))
        elif kind == "tag":
            tag(b, x + 38, yy - 4, arg)
        elif kind == "pause":
            pause_icon(b, x + 11, yy - 11)
        b.append(text(x + 46, yy, lab, "note sm", anchor="start"))


# ===================================================================== Module 12


def thresholds(c: dict) -> tuple[float, float, float]:
    """eq-three-thresholds and Chow's lambda* (Module 12, section 3)."""
    tau_act = 1 - c["ask"] / (c["wrong"] - c["miss"])
    tau_esc = 1 - (c["esc"] - c["ask"]) / c["miss"]
    lam = 1 - c["esc"] / c["wrong"]
    return tau_esc, tau_act, lam


def three_costs(p: float, c: dict) -> dict:
    """eq-three-costs."""
    return {
        "act": (1 - p) * c["wrong"],
        "ask": c["ask"] + (1 - p) * c["miss"],
        "escalate": c["esc"],
    }


def half_up(v: float, places: int) -> str:
    """Round as the page does (0.96875 -> 0.969), not to even."""
    return str(Decimal(v).quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP))


def fig_act_ask_escalate() -> str:
    costs = dict(wrong=20.0, ask=0.5, miss=4.0, esc=3.0)  # Module 12's worked example
    tau_esc, tau_act, lam = thresholds(costs)
    # The page states these values; the lines must cross exactly there.
    assert (half_up(tau_esc, 3), half_up(tau_act, 3), half_up(lam, 2)) == ("0.375", "0.969", "0.85")
    c_esc, c_act, c_lam = (
        three_costs(tau_esc, costs),
        three_costs(tau_act, costs),
        three_costs(lam, costs),
    )
    assert abs(c_esc["ask"] - c_esc["escalate"]) < 1e-12
    assert abs(c_act["ask"] - c_act["act"]) < 1e-12
    assert abs(c_lam["act"] - c_lam["escalate"]) < 1e-12
    for i in range(1001):  # the three-region rule picks the cheapest action everywhere
        p = i / 1000
        c = three_costs(p, costs)
        rule = "act" if p >= tau_act else ("escalate" if p < tau_esc else "ask")
        assert c[rule] <= min(c.values()) + 1e-12, p

    W, H = 760, 424
    X0, X1, Y0, Y1 = 78, 728, 360, 60  # plot box: p in [0, 1], cost in [0, 20]

    def px(p):
        return X0 + p * (X1 - X0)

    def py(v):
        return Y0 - v * (Y0 - Y1) / 20

    b: list[str] = []
    # regions of the rule, full height, labeled at the top
    regions = [
        ("escalate", 0.0, tau_esc, "#eef1f4", "#d3dae2"),
        ("ask", tau_esc, tau_act, "#fcf2ea", "#f1d3bd"),
        ("act", tau_act, 1.0, "#e6edf5", "#c2d1e3"),
    ]
    for _name, a, z, band, _ in regions:
        b.append(
            f'<rect x="{f(px(a))}" y="{Y1}" width="{f(px(z) - px(a))}" height="{Y0 - Y1}" fill="{band}"/>'
        )
    # grid and axes
    for v in (5, 10, 15, 20):
        b.append(line(X0, py(v), X1, py(v), cls="rule", mk=None, extra=' style="stroke-width:1"'))
    # the lower envelope, shaded underneath, region by region
    for _name, a, z, _, fill in regions:
        pts = [(a, 0.0), (a, min(three_costs(a, costs).values()))]
        if a < tau_esc < z:
            pts.append((tau_esc, costs["esc"]))
        pts += [(z, min(three_costs(z, costs).values())), (z, 0.0)]
        d = " ".join(f"{f(px(p))},{f(py(v))}" for p, v in pts)
        b.append(f'<polygon points="{d}" fill="{fill}"/>')
    for name, a, z, _, _ in regions:
        cx = (px(a) + px(z)) / 2
        b.append(text(cx, Y1 - 9, name, "b", size=14.5))
    # thresholds
    for v in (tau_esc, tau_act):
        b.append(
            line(
                px(v),
                Y1,
                px(v),
                Y0,
                cls="ln",
                mk=None,
                extra=f' style="stroke:{INK};stroke-dasharray:5 4"',
            )
        )
    b.append(
        M(
            px(tau_esc) + 7,
            Y1 + 24,
            f"τ_\\r{{esc}} = \\t{{{half_up(tau_esc, 3)}}}",
            size=15,
            anchor="start",
        )
    )
    b.append(
        M(
            px(tau_act) - 7,
            Y1 + 24,
            f"τ_\\r{{act}} = \\t{{{half_up(tau_act, 3)}}}",
            size=15,
            anchor="end",
        )
    )
    b.append(line(px(lam), Y1 + 44, px(lam), Y0, cls="dotted", mk=None))
    b.append(text(px(lam) - 7, Y1 + 60, "two-action rule", "note sm", anchor="end"))
    b.append(
        M(
            px(lam) - 7,
            Y1 + 77,
            f"\\t{{Chow's }}λ^* = \\t{{{half_up(lam, 2)}}}",
            size=14,
            anchor="end",
            cls="note",
        )
    )
    # the three cost lines (eq-three-costs): color, dash and a direct label each
    ends = {
        k: (three_costs(0.0, costs)[k], three_costs(1.0, costs)[k])
        for k in ("act", "ask", "escalate")
    }
    styles = {
        "act": f"stroke:{NAVY};stroke-width:2.2",
        "ask": f"stroke:{ACCENT};stroke-width:2.2;stroke-dasharray:8 4",
        "escalate": f"stroke:{MUTED};stroke-width:2.2;stroke-dasharray:2 3",
    }
    for k, (v0, v1) in ends.items():
        b.append(
            line(px(0), py(v0), px(1), py(v1), cls="ln", mk=None, extra=f' style="{styles[k]}"')
        )
    b.append(M(X0 + 14, 170, "\\t{act: }(1 − p̂) ℓ_\\r{wrong}", size=15, anchor="start", cls="halo"))
    b.append(
        M(
            X0 + 14,
            py(5.4),
            "\\t{ask: }ℓ_\\r{ask} + (1 − p̂) ℓ_\\r{miss}",
            size=15,
            anchor="start",
            cls="halo",
        )
    )
    b.append(
        M(px(0.43), py(3) - 8, "\\t{escalate: }ℓ_\\r{esc}", size=15, anchor="start", cls="halo")
    )
    # where the cheapest line changes
    b.append(dot(px(tau_esc), py(costs["esc"]), 4.2, INK))
    b.append(dot(px(tau_act), py(c_act["act"]), 4.2, INK))
    b.append(
        f'<circle cx="{f(px(lam))}" cy="{f(py(costs["esc"]))}" r="4" fill="#ffffff" stroke="{MUTED}" stroke-width="1.6"/>'
    )
    # axes, ticks, titles
    b.append(line(X0, Y0, X1, Y0, cls="ln", mk=None, extra=f' style="stroke:{MUTED}"'))
    b.append(line(X0, Y0, X0, Y1, cls="ln", mk=None, extra=f' style="stroke:{MUTED}"'))
    for k in range(6):
        p = k / 5
        b.append(
            line(px(p), Y0, px(p), Y0 + 5, cls="ln", mk=None, extra=f' style="stroke:{MUTED}"')
        )
        b.append(text(px(p), Y0 + 21, f"{p:.1f}", "note sm"))
    for v in (0, 5, 10, 15, 20):
        b.append(text(X0 - 9, py(v) + 4.5, str(v), "note sm", anchor="end"))
    b.append(M((X0 + X1) / 2, Y0 + 50, "\\t{probability that the answer is right, }p̂", size=15))
    b.append(
        text(
            24,
            (Y0 + Y1) / 2,
            "expected cost per case",
            "sm",
            extra=f' transform="rotate(-90 24 {f((Y0 + Y1) / 2)})"',
        )
    )
    b.append(
        M(
            X1,
            24,
            "\\t{costs of the worked example: }ℓ_\\r{wrong} = \\t{20, }ℓ_\\r{ask} = \\t{0.5, }ℓ_\\r{miss} = \\t{4, }ℓ_\\r{esc} = \\t{3}",
            size=14,
            anchor="end",
            cls="note",
        )
    )
    return figure(
        W,
        H,
        "Act, ask or escalate: expected cost against the probability",
        "A computed plot, not a measurement. The horizontal axis is p-hat, the probability that the answer is "
        "right, from 0 to 1; the vertical axis is the expected cost per case, from 0 to 20. Three straight lines "
        "use the worked example's costs (l_wrong 20, l_ask 0.5, l_miss 4, l_esc 3): act, (1 - p-hat) times 20, "
        "falls from 20 to 0; ask, 0.5 + (1 - p-hat) times 4, falls from 4.5 to 0.5; escalate is flat at 3. The "
        "lowest line at each p-hat is shaded: escalate below tau_esc = 0.375, ask between 0.375 and "
        "tau_act = 0.969, act above 0.969. Dashed vertical lines mark the two thresholds. A dotted line at "
        "Chow's lambda* = 0.85, where act and escalate cross, is labeled two-action rule; there the ask line "
        "is lower than both.",
        b,
    )


def fig_route_guard_verify() -> str:
    W, H = 860, 446
    b: list[str] = []
    yr = 236  # the router's row
    thr = [(0.375, "τ_\\r{esc}"), (0.969, "τ_\\r{act}")]
    # the request and the router
    b.append(rect(12, yr - 26, 78, 52, "op", rx=8))
    b.append(text(51, yr - 3, "user", "b", size=14))
    b.append(text(51, yr + 15, "request", "b", size=14))
    b.append(line(90, yr, 110, yr))
    decision(
        b, 112, yr - 59, 172, "router", "Choice", "what should happen next?", 0.6, thr, plabel="p̂"
    )
    tag(b, 284, yr - 72, "Lab 14 · Ex. 2")
    # the router's five next steps, fanned out from one bus
    xb, xt = 302, 328
    ys = {"retrieve": 42, "calculate": 104, "guard": yr, "ask_user": 340, "escalate": 392}
    b.append(line(284, yr, xb, yr, mk=None))
    b.append(path(f"M{xb},{ys['retrieve']} V{ys['escalate']}", mk=None))
    for y in ys.values():
        b.append(line(xb, y, xt - 2, y))
    b.append(dot(xb, yr, 3.2))
    node(b, xt, 22, 104, 40, "box", "retrieve", mono=True, size=14)
    node(b, xt, 84, 104, 40, "box", "calculate", mono=True, size=14)
    node(b, xt, 320, 120, 40, "op", "ask_user", mono=True, size=14)
    node(b, xt, 372, 120, 40, "op", "escalate", mono=True, size=14)
    b.append(text(xt + 128, 345, "ask the user", "note sm", anchor="start"))
    b.append(text(xt + 128, 397, "to a person", "note sm", anchor="start"))
    # retrieve and calculate feed the generative model, then the verifier
    ya = 74
    b.append(path(f"M432,{ys['retrieve']} H446 V{ya}", mk=None))
    b.append(path(f"M432,{ys['calculate']} H446 V{ya}", mk=None))
    b.append(dot(446, ya, 3.2))
    b.append(line(446, ya, 462, ya))
    node(b, 464, ya - 28, 112, 56, "abox", "LLM answer", "generative model")
    b.append(line(576, ya, 598, ya))
    decision(
        b, 600, ya - 59, 172, "verify", "Noul", "supported by the sources?", 0.6, thr, plabel="p̂"
    )
    tag(b, 772, ya - 72, "Lab 15 · Ex. 1")
    b.append(line(740, ya + 59, 740, 156))
    b.append(M(748, 150, "p̂ ≥ τ_\\r{act}", size=14, anchor="start", cls="note"))
    node(b, 690, 158, 160, 36, "op", "deliver the answer", size=14)
    # the guard in front of the risky tool
    decision(b, xt, yr - 59, 172, "guard", "Noul", "may this action run?", 0.6, thr, plabel="p̂")
    tag(b, xt + 172, yr - 72, "Lab 14 · Ex. 2")
    b.append(line(500, yr, 554, yr))
    b.append(M(527, yr - 8, "p̂ ≥ τ_\\r{act}", size=14, cls="note"))
    node(b, 556, yr - 22, 124, 44, "box", "send_email", "a risky tool", mono=True, size=14)
    # key and note
    legend(
        b,
        14,
        318,
        [
            ("box", "dbox", "decision model: returns a probability"),
            ("box", "abox", "generative model: writes text"),
            ("box", "box", "tool or step"),
            ("box", "op", "hand-off or output"),
            ("tag", "Ex. 2", "where a lab builds it"),
        ],
    )
    for k, s in enumerate(
        [
            "\\t{Each decision model compares its }p̂\\t{ with}",
            "\\t{its own thresholds: act at }p̂ ≥ τ_\\r{act}\\t{,}",
            "\\t{ask a person between }τ_\\r{esc}\\t{ and }τ_\\r{act}\\t{,}",
            "\\t{escalate below }τ_\\r{esc}\\t{ (section 3). Only the}",
            "\\t{act exits of guard and verify are drawn.}",
        ]
    ):
        b.append(M(570, 336 + 18 * k, s, size=13.5, anchor="start", cls="note"))
    b = ['<g transform="translate(0,18)">', *b, "</g>"]
    return figure(
        W,
        H,
        "Where a decision model fits: route, guard, verify",
        "A left-to-right system diagram. A user request enters the router, a decision model that answers a Choice "
        "question, what should happen next. Its five next steps fan out: retrieve, calculate, the guard in front "
        "of send_email, ask_user and escalate to a person. Retrieve and calculate feed an LLM answer, a "
        "generative model, which is followed by verify, a decision model that answers a Noul question: is the "
        "answer supported by the sources? If p-hat is at least tau_act, the answer is delivered. The guard, a decision "
        "model with a Noul question, may this action run, stands before the risky send_email tool, which runs if "
        "p-hat is at least tau_act. Each decision-model box carries a gauge for its probability p-hat with two threshold "
        "ticks, tau_esc and tau_act. Tags note where the labs build each one: the router and the guard in Lab 14, "
        "Exercise 2, the verifier in Lab 15, Exercise 1. A note says that between tau_esc and tau_act the system "
        "asks a person, and below tau_esc it escalates; only the act exits of guard and verify are drawn.",
        b,
    )


# ===================================================================== Module 13


def fig_rag_pipeline() -> str:
    W, H = 860, 370
    b: list[str] = []
    # lanes
    b.append(rect(10, 30, 840, 116, "panel", rx=12))
    b.append(text(26, 52, "once, offline (indexing)", "note b", anchor="start"))
    b.append(rect(10, 192, 840, 116, "panel", rx=12))
    b.append(text(26, 214, "per query", "note b", anchor="start"))
    # indexing
    yt = 70
    node(b, 26, yt, 140, 58, "box", "load", "documents")
    node(b, 214, yt, 140, 58, "box", "chunk", "\\t{chunks }c_\\t{1} … c_M", math=True)
    node(b, 402, yt, 140, 58, "box", "embed", "\\t{vectors }h_c", math=True)
    node(b, 590, yt, 240, 58, "box", "index", "vector store + BM25 index")
    for xa, xb in [(166, 212), (354, 400), (542, 588)]:
        b.append(line(xa, yt + 29, xb, yt + 29))
    b.append(path(f"M214,{yt - 8} V{yt - 13} H830 V{yt - 8}", cls="rule", mk=None))
    tag(b, 830, yt - 13, "Ex. 2: build_index")
    # per query
    yq = 232
    b.append(rect(26, yq + 6, 92, 46, "op", rx=23))
    b.append(M(72, yq + 35, "\\t{question }q", size=14))
    node(b, 156, yq, 150, 58, "box", "retrieve", "\\t{top }k_\\t{0}\\t{ candidates}", math=True)
    tag(b, 302, yq, "Ex. 2, 3")
    node(b, 344, yq, 150, 58, "box", "rerank", "\\t{keep the top }k", math=True)
    tag(b, 490, yq, "Ex. 4")
    node(b, 532, yq, 150, 58, "abox", "generate", "LLM, numbered sources")
    tag(b, 678, yq, "Ex. 5")
    node(b, 720, yq, 112, 58, "op", "answer", "with citations")
    for xa, xb in [(118, 154), (306, 342), (494, 530), (682, 718)]:
        b.append(line(xa, yq + 29, xb, yq + 29))
    # retrieve reads the index
    b.append(path(f"M190,{yq} V170 H710 V{yt + 60}"))
    b.append(
        M(450, 164, "\\t{score every chunk against }q\\t{, from the index}", size=14, cls="note")
    )
    # what measures each half
    yb = 326
    b.append(path(f"M156,{yb - 8} V{yb - 3} H494 V{yb - 8}", cls="rule", mk=None))
    b.append(text(325, yb + 14, "measured by recall@k, MRR (section 8; Ex. 1)", "note sm"))
    b.append(path(f"M532,{yb - 8} V{yb - 3} H832 V{yb - 8}", cls="rule", mk=None))
    b.append(text(682, yb + 14, "measured by faithfulness, relevance,", "note sm"))
    b.append(text(682, yb + 30, "correctness (section 9)", "note sm"))
    return figure(
        W,
        H,
        "The RAG pipeline",
        "Two horizontal lanes. Top lane, once, offline (indexing): load (documents), chunk (chunks c_1 to c_M), "
        "embed (vectors h_c) and index (vector store and BM25 index); chunk, embed and index are tagged Ex. 2, "
        "build_index. Bottom lane, per query: the question q goes to retrieve (top k_0 candidates), which reads "
        "the index through an arrow up into it; then rerank (keep the top k), generate (an LLM with numbered "
        "sources) and the answer with citations. Retrieve is tagged Ex. 2 and 3, rerank Ex. 4, generate Ex. 5. "
        "Under retrieve and rerank: measured by recall@k and MRR (section 8; Ex. 1). Under generate and the "
        "answer: measured by faithfulness, relevance and correctness (section 9). Retrieval stages are blue, "
        "generation is orange.",
        b,
    )


def _vector(b, x, y, n=5, fill="#ffffff", stroke=NAVY) -> None:
    for k in range(n):
        b.append(
            f'<rect x="{f(x + 13 * k)}" y="{f(y)}" width="13" height="15" fill="{fill}" stroke="{stroke}" stroke-width="1.1"/>'
        )


def fig_bi_vs_cross() -> str:
    W, H = 820, 372
    b: list[str] = []
    # left panel: bi-encoder
    b.append(rect(10, 10, 392, 352, "panel", rx=12))
    b.append(text(26, 36, "bi-encoder (retrieve)", "b", anchor="start", size=15))
    tag(b, 392, 30, "Ex. 2, 3")
    xq, xc = 110, 302
    for x, s in [(xq, "\\t{query }q"), (xc, "\\t{chunk }c")]:
        b.append(rect(x - 46, 56, 92, 30, "op", rx=15))
        b.append(M(x, 76, s, size=14))
        b.append(line(x, 86, x, 108))
        node(b, x - 58, 110, 116, 48, "box", "encoder", "f", math=True, size=14.5)
        b.append(line(x, 158, x, 180))
    b.append(text(206, 130, "same", "note sm"))
    b.append(text(206, 147, "weights", "note sm"))
    _vector(b, xq - 32, 182)
    _vector(b, xc - 32, 182)
    b.append(M(xq - 42, 195, "h_q", size=15, anchor="end"))
    b.append(M(xc + 42, 195, "h_c", size=15, anchor="start"))
    # dot product
    yd = 262
    b.append(line(xq, 197, 196, yd - 10))
    b.append(line(xc, 197, 216, yd - 10))
    b.append(f'<circle class="op" cx="206" cy="{yd}" r="13"/>')
    b.append(dot(206, yd, 3.2))
    b.append(text(184, yd + 5, "dot product", "note sm", anchor="end"))
    b.append(line(206, yd + 13, 206, yd + 36))
    b.append(M(206, yd + 56, "s_\\r{dense} = h_q^⊤ h_c", size=16))
    for k, s in enumerate(["chunk vectors", "computed once,", "offline"]):
        b.append(text(290, 226 + 16 * k, s, "note sm", anchor="start"))
    b.append(text(206, 350, "one encoder pass per query", "note sm"))
    # right panel: cross-encoder
    x0 = 418
    b.append(rect(x0, 10, 392, 352, "panel", rx=12))
    b.append(text(x0 + 16, 36, "cross-encoder (rerank)", "b", anchor="start", size=15))
    tag(b, x0 + 382, 30, "Ex. 4")
    toks = [("[CLS]", 56, "mono"), ("q", 72, "m"), ("[SEP]", 56, "mono"), ("c", 112, "m")]
    x = x0 + 46
    centers = []
    for s, w, cls in toks:
        b.append(rect(x, 56, w, 30, "op", rx=5))
        if cls == "m":
            b.append(M(x + w / 2, 77, s, size=15))
        else:
            b.append(text(x + w / 2, 76, s, "mono", size=13))
        centers.append(x + w / 2)
        b.append(line(x + w / 2, 86, x + w / 2, 108))
        x += w + 6
    xe0, xe1 = x0 + 34, x0 + 358
    b.append(rect(xe0, 110, xe1 - xe0, 52, "box", rx=6))
    b.append(text((xe0 + xe1) / 2, 132, "encoder", "b", size=14.5))
    b.append(
        M(
            (xe0 + xe1) / 2,
            151,
            "\\t{every layer attends across }q\\t{ and }c",
            size=13.5,
            cls="note",
        )
    )
    # outputs: only the [CLS] vector is used
    b.append(line(centers[0], 162, centers[0], 184))
    _vector(b, centers[0] - 32, 186, fill="#f8e9de", stroke=ACCENT)
    for cx in centers[1:]:
        b.append(line(cx, 162, cx, 176, cls="dln", mk=None))
    b.append(text(centers[1] - 6, 199, "other outputs unused", "note sm", anchor="start"))
    b.append(M(centers[0] - 40, 199, "\\t{CLS}", size=12.5, anchor="end", cls="note"))
    b.append(line(centers[0], 201, centers[0], 232))
    b.append(rect(centers[0] - 22, 234, 44, 28, "op", rx=5))
    b.append(M(centers[0], 253, "w", size=15))
    b.append(text(centers[0] + 32, 253, "linear head", "note sm", anchor="start"))
    b.append(line(centers[0], 262, centers[0], yd + 36))
    b.append(
        M(
            centers[0] - 14,
            yd + 56,
            "s_\\r{cross} = w^⊤ \\r{Enc}([\\t{CLS}] q [\\t{SEP}] c)_\\t{CLS}",
            size=16,
            anchor="start",
        )
    )
    b.append(text(x0 + 196, 350, "one pass per (query, chunk) pair", "note sm"))
    return figure(
        W,
        H,
        "Bi-encoder against cross-encoder",
        "Two panels. Left, bi-encoder (retrieve), used in Exercises 2 and 3: the query q and the chunk c each pass "
        "through an encoder f; the two encoders share the same weights and are shaded alike. Each emits a vector, "
        "h_q and h_c, and a dot product combines them into s_dense = h_q transpose h_c. Notes: chunk vectors "
        "computed once, offline; one encoder pass per query. Right, cross-encoder (rerank), used in Exercise 4: one "
        "encoder reads the single input [CLS] q [SEP] c, and every layer attends across q and c. Only the output "
        "at the CLS position is used: a linear head w turns it into s_cross. Note: one pass per (query, chunk) "
        "pair.",
        b,
    )


# ===================================================================== Module 14


def fig_desk_agent() -> str:
    W, H = 860, 784
    b: list[str] = []
    cx = 400
    # trust boundary (drawn first, under everything)
    b.append(rect(52, 372, 478, 356, "bound", rx=12))
    for k, parts in enumerate(
        [
            [("trust boundary: every", "")],
            [("send_email", "mono"), (" passes the guard,", "")],
            [("whatever asked for it", "")],
        ]
    ):
        b.append(rich(66, 394 + 17 * k, parts, "note sm", anchor="start"))
    # START and the router
    pill(b, cx, 24, "START")
    b.append(line(cx, 37, cx, 60))
    decision(
        b,
        295,
        62,
        210,
        "router",
        "Choice",
        "which next step?",
        0.91,
        [(0.75, "τ_\\r{route}")],
        plabel="p̂_\\r{route}",
        mono=True,
    )
    tag(b, 501, 62, "Ex. 2")
    # router -> agent / ask_user / escalate
    b.append(line(cx, 180, cx, 246, cls="cln"))
    b.append(
        M(
            cx - 8,
            204,
            "p̂_\\r{route} ≥ τ_\\r{route}\\t{, and the route is}",
            size=14,
            anchor="end",
            cls="note",
        )
    )
    b.append(
        rich(
            cx - 8,
            222,
            [
                ("retrieve", "mono"),
                (", ", ""),
                ("calculate", "mono"),
                (" or ", ""),
                ("send_email", "mono"),
            ],
            "note sm",
            anchor="end",
        )
    )
    node(b, 665, 96, 120, 40, "op", "ask_user", None, mono=True, size=14)
    b.append(line(505, 116, 663, 116, cls="cln"))
    b.append(rich(584, 108, [("route is ", ""), ("ask_user", "mono")], "note sm"))
    b.append(M(584, 134, "p̂_\\r{route} ≥ τ_\\r{route}", size=14, cls="note"))
    node(b, 665, 533, 120, 40, "op", "escalate", None, mono=True, size=14)
    b.append(path("M505,76 H840 V553 H787", cls="cln"))
    b.append(
        M(
            744,
            68,
            "p̂_\\r{route} < τ_\\r{route}\\t{, or the route is}",
            size=14,
            anchor="end",
            cls="note",
        )
    )
    b.append(text(748, 68, "escalate", "note sm mono", anchor="start"))
    # the agent and END
    node(b, 300, 248, 200, 60, "abox", "agent", "language model with tools", mono=True)
    pill(b, 725, 278, "END")
    b.append(line(500, 278, 696, 278, cls="cln"))
    b.append(text(598, 270, "answer, cut off or refused,", "note sm"))
    b.append(M(598, 297, "\\t{or }k = K_\\r{max}", size=14, cls="note"))
    b.append(line(725, 136, 725, 263))
    b.append(line(725, 533, 725, 293))
    # agent <-> tools
    node(b, 295, 392, 210, 50, "box", "tools", "runs each call; parks send_email", mono=True)
    tag(b, 501, 392, "Ex. 1")
    b.append(line(370, 308, 370, 390, cls="cln"))
    b.append(text(362, 354, "tool calls", "note sm", anchor="end"))
    b.append(line(430, 392, 430, 310, cls="cln"))
    b.append(rich(438, 354, [("no ", ""), ("send_email", "mono")], "note sm", anchor="start"))
    # tools -> guard
    b.append(line(cx, 442, cx, 494, cls="cln"))
    b.append(rich(cx - 8, 472, [("send_email", "mono"), (" pending", "")], "note sm", anchor="end"))
    decision(
        b,
        295,
        496,
        210,
        "guard",
        "Noul",
        "may this email be sent now?",
        0.80,
        [(0.375, "τ_\\r{esc}"), (0.969, "τ_\\r{act}")],
        plabel="p_\\r{allow}",
        mono=True,
    )
    tag(b, 501, 496, "Ex. 2")
    # guard -> escalate / send / human_review
    b.append(line(505, 553, 663, 553, cls="cln"))
    b.append(M(597, 545, "p_\\r{allow} < τ_\\r{esc}", size=14, cls="note"))
    b.append(text(597, 571, "or rule P6 fails", "note sm"))
    b.append(line(cx, 614, cx, 666, cls="cln"))
    b.append(M(cx + 8, 644, "p_\\r{allow} ≥ τ_\\r{act}", size=14, anchor="start", cls="note"))
    b.append(path("M295,553 H140 V666", cls="cln"))
    b.append(M(218, 545, "τ_\\r{esc} ≤ p_\\r{allow} < τ_\\r{act}", size=14, cls="note"))
    node(b, 330, 668, 140, 44, "box", "send", "mock send_email", mono=True)
    b.append(rect(60, 668, 160, 44, "op", rx=8))
    pause_icon(b, 76, 683)
    b.append(text(150, 695, "human_review", "b mono", size=14))
    tag(b, 216, 668, "Ex. 3")
    b.append(line(220, 690, 328, 690, cls="cln"))
    b.append(text(274, 682, "approve", "note sm"))
    # back to the agent: reject (dashed) and send's result (solid)
    b.append(path("M60,690 H40 V292 H298", cls="cln"))
    b.append(text(60, 310, "reject: an error result for the call", "note sm", anchor="start"))
    b.append(path("M400,712 V738 H24 V264 H298"))
    # what is not drawn, and the key
    b.append(text(612, 604, "Not drawn: a decider error", "note sm", anchor="start"))
    b.append(text(612, 621, "escalates (fails closed).", "note sm", anchor="start"))
    legend(
        b,
        612,
        652,
        [
            ("line", "ln", "fixed edge"),
            ("line", "cln", "conditional edge"),
            ("box", "dbox", "decision model"),
            ("box", "abox", "language model"),
            ("pause", None, "pauses for a person"),
            ("tag", "Ex. 2", "written in Exercise 2"),
        ],
    )
    return figure(
        W,
        H,
        "The desk agent as a graph",
        "A top-to-bottom graph. START leads to router, a decision model that answers a Choice: which next step. Its "
        "gauge shows p-hat_route against one threshold, tau_route. Dashed conditional edges leave the router: to "
        "agent if p-hat_route is at least tau_route and the route is retrieve, calculate or send_email; to "
        "ask_user if the route is ask_user; to escalate if p-hat_route is below tau_route or the route is "
        "escalate. Agent, the language model with tools, goes to END on an answer, a cut-off or refused reply, or "
        "k = K_max, and to tools on tool calls. Tools runs each call but parks send_email: with no send_email it "
        "returns to agent, and with send_email pending it goes to guard, a decision model that answers a Noul: "
        "may this email be sent now. Its gauge shows p_allow against tau_esc and tau_act. Guard goes to send if "
        "p_allow is at least tau_act, to human_review if p_allow is between tau_esc and tau_act, and to escalate "
        "if p_allow is below tau_esc or rule P6 fails. Human_review, marked with a pause icon, goes to send on "
        "approve and back to agent on reject, with an error result for the call. Solid fixed edges: START to "
        "router, send to agent, ask_user to END, escalate to END. A dotted rectangle around tools, guard, "
        "human_review and send is labeled: trust boundary, every send_email passes the guard, whatever asked "
        "for it. Tags: Ex. 2 on router and guard, Ex. 1 on tools, Ex. 3 on human_review. A note says that a decider error "
        "also escalates (fails closed).",
        b,
    )


# ===================================================================== Module 15


def fig_capstone() -> str:
    W, H = 860, 474
    b: list[str] = []
    yc = 178  # the main row (the whole drawing is moved up 18 px at the end)
    pill(b, 34, yc, "START")
    b.append(line(61, yc, 80, yc))
    decision(
        b,
        82,
        yc - 59,
        156,
        "plan",
        "Noul",
        "needs two documents?",
        0.3,
        [(0.5, "τ_\\r{plan}")],
        plabel="p_\\r{multi}",
        mono=True,
    )
    b.append(M(160, yc + 80, "p_\\r{multi} ≥ τ_\\r{plan}\\t{:}", size=14, cls="note"))
    b.append(text(160, yc + 97, "split into two queries", "note sm"))
    b.append(line(238, yc, 266, yc))
    node(
        b, 268, yc - 28, 136, 56, "box", "retrieve", "k\\t{ chunks per query}", mono=True, math=True
    )
    b.append(line(404, yc, 430, yc))
    node(b, 432, yc - 28, 122, 56, "abox", "answer", "generator: a draft", mono=True)
    b.append(line(554, yc, 596, yc, cls="cln"))
    b.append(text(575, yc - 8, "draft", "note sm"))
    decision(
        b,
        598,
        yc - 59,
        156,
        "verify",
        "Noul",
        "every claim supported?",
        0.85,
        [(0.8, "τ_\\r{verify}")],
        plabel="p_\\r{sup}",
        mono=True,
    )
    tag(b, 750, yc - 59, "Ex. 1")
    # retry: back to retrieve with twice the chunks
    b.append(path(f"M640,{yc - 59} V70 H336 V{yc - 30}", cls="cln"))
    b.append(
        M(486, 61, "p_\\r{sup} < τ_\\r{verify}\\t{, retry left: }k → \\t{2}k", size=14, cls="note")
    )
    # the outputs
    yo = 352
    node(b, 540, yo - 20, 100, 40, "op", "abstain", None, mono=True, size=14)
    pill(b, 693, yo, "END")
    node(b, 748, yo - 20, 96, 40, "op", "deliver", None, mono=True, size=14)
    b.append(line(640, yo, 664, yo))
    b.append(line(748, yo, 722, yo))
    b.append(path(f"M493,{yc + 28} V{yo} H538", cls="cln"))
    b.append(text(485, 268, "abstention", "note sm", anchor="end"))
    b.append(text(485, 285, "sentence, or", "note sm", anchor="end"))
    b.append(text(485, 302, "no draft", "note sm", anchor="end"))
    b.append(line(620, yc + 59, 620, yo - 22, cls="cln"))
    b.append(M(612, 268, "p_\\r{sup} < τ_\\r{verify}\\t{,}", size=14, anchor="end", cls="note"))
    b.append(text(612, 285, "no retry left", "note sm", anchor="end"))
    b.append(path(f"M754,{yc + 30} H796 V{yo - 22}", cls="cln"))
    b.append(M(788, 268, "p_\\r{sup} ≥ τ_\\r{verify}", size=14, anchor="end", cls="note"))
    # the scorer, outside the system
    ys = 412
    b.append(rect(470, ys, 380, 70, "bound", rx=10))
    b.append(text(484, ys + 20, "scorer (fixed, outside the system)", "note sm b", anchor="start"))
    for x, s in [(486, "reference judge"), (664, "key-fact check")]:
        b.append(rect(x, ys + 30, 168, 30, "op", rx=5))
        b.append(text(x + 84, ys + 50, s, "sm"))
    b.append(line(590, yo + 20, 590, ys - 2, cls="dotted", mk="c"))
    b.append(line(796, yo + 20, 796, ys - 2, cls="dotted", mk="c"))
    # key and what is not drawn
    legend(
        b,
        16,
        336,
        [
            ("line", "ln", "fixed edge"),
            ("line", "cln", "conditional edge"),
            ("box", "dbox", "decision model"),
            ("box", "abox", "generator (language model)"),
            ("box", "box", "retriever"),
        ],
    )
    b.append(text(16, 464, "Not drawn: a node that raises ends the run", "note sm", anchor="start"))
    b.append(
        text(16, 481, "(an error); a failed decision call abstains.", "note sm", anchor="start")
    )
    b = ['<g transform="translate(0,-18)">', *b, "</g>"]
    return figure(
        W,
        H,
        "The capstone starter system as a graph",
        "A left-to-right graph. START leads to plan, a decision model that answers a Noul: does the question need "
        "two documents? Its gauge shows p_multi against tau_plan; if p_multi is at least tau_plan, the question is "
        "split into two queries. Plan leads to retrieve (k chunks per query), retrieve to answer, the generator, "
        "which writes a draft. Dashed conditional edges: answer goes to verify with a draft, or to abstain on the "
        "abstention sentence or no draft. Verify, a decision model that answers a Noul, is every claim supported, "
        "shows p_sup against tau_verify and is tagged Ex. 1. It goes to deliver if p_sup is at least tau_verify; "
        "back to retrieve if p_sup is below tau_verify and a retry is left, with k doubled; and to abstain if no "
        "retry is left. Deliver and abstain lead to END. Below, a dotted box labeled scorer (fixed, outside the "
        "system) holds a reference judge and a key-fact check, with dotted arrows from deliver and abstain into "
        "it: the system's verifier and the scorer's judge are different. A note says that a node that raises "
        "ends the run with an error, and a failed decision call abstains.",
        b,
    )


FIGURES = {
    "12-act-ask-escalate.svg": fig_act_ask_escalate,
    "12-route-guard-verify.svg": fig_route_guard_verify,
    "13-rag-pipeline.svg": fig_rag_pipeline,
    "13-bi-vs-cross-encoder.svg": fig_bi_vs_cross,
    "14-desk-agent-graph.svg": fig_desk_agent,
    "15-capstone-graph.svg": fig_capstone,
}


def main() -> None:
    for name, fn in FIGURES.items():
        (IMAGES / name).write_text(fn(), encoding="utf-8")
        print(f"wrote images/{name}")


if __name__ == "__main__":
    main()
