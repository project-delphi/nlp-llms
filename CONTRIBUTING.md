# Contributing

Thank you for helping improve this workshop. Corrections, clearer explanations and bug reports are all welcome.

## Where to edit

| To change | Edit | Then |
|---|---|---|
| A module's title, duration, objectives or summary | `_variables.yml` | Run both generators |
| The schedule | `_variables.yml` (`schedule`, `days`) | Run `gen_tables.py` |
| Briefing content | `modules/NN-slug.qmd` | `quarto preview` |
| A lab | `notebooks/NN-slug.ipynb`, any cell except the four generated ones (below) | Run `gen_notebooks.py` |
| A figure | the `scripts/make_figures_*.py` script that draws it (the SVG in `images/` is its output) | Run that script |
| Site pages | the `.qmd` file at the repository root | `quarto preview` |

Do not edit anything under `_includes/`, the four generated cells of a notebook, or the region between the `BEGIN modules` and `END modules` markers in `README.md`. The four cells are the header, the harness cell after it, the summary cell before the footer, and the footer; each is tagged `generated`. They are generated, and CI fails if they differ from what the generators produce.

## Notebook rules

- A notebook runs top to bottom on a fresh free-tier Colab runtime with no API keys set.
- Anything Colab does not preinstall is installed in the setup cell with a pinned version.
- Each exercise is a `# TODO N` cell (tag `exercise`) that defines a stub, followed by a folded solution cell (tag `solution`), a short "why this works" note, and a checkpoint cell (tag `checkpoint`).
- **The solution never replaces the participant's code.** Mark each definition in a solution cell with `@workshop.solution(N)`, as its outermost decorator, below the `#@title` line. For a value rather than a function or class, use `name = workshop.solution_value(N, "name", value)`. The harness cell that `scripts/gen_notebooks.py` writes at the top of every notebook stores the reference, and binds it only when `WORKED_EXAMPLE` is ticked or `NLP_LLMS_WORKED=1` (CI's default). A stuck participant calls `workshop.use_reference(N)`.
- **A stub must not raise when it is defined.** Calling an unfinished pure stub must raise `NotImplementedError("TODO N")`. A partial stub (some lines given) may simply return a wrong value: its checkpoint must catch that.
- **A hint, where participants are likely to stall.** One markdown cell tagged `hint`, above the `# TODO N` cell, folded: `<details>` with the summary `Hint for TODO N`. It names the principle or the briefing section to check, and may give a tiny counterexample of a common wrong version; it never gives the code. The harness tells a participant whose checkpoint failed that the hint is there.
- **A checkpoint's assertion message says what to inspect.** Show the observed and the expected value, and name the likely mistake: `f"rows must sum to 1 over the keys; got {A.sum(-1)[:3]}"`, not a bare `assert`.
- **The first statement of a checkpoint cell is `workshop.checkpoint(N)`**, or `workshop.checkpoint(N, label="3b")`, or `workshop.checkpoint(label="...")` for a check on code the lab provides. The cell then reports whether it checked the participant's code or the reference.
- **Run the three modes before you open a pull request:**
  - `scripts/test_notebooks.py` (worked);
  - `--learner` (the run must stop at the first TODO);
  - `--verify-checkpoints` (each exercise's first checkpoint must fail on its stub).

  `tests/test_exercises.py` checks the structure. Migrate an older lab with `scripts/migrate_exercises.py`.
- One optional stretch section, last.
- API keys come from Colab Secrets. Never write a key into a cell.
- Notebooks are committed without outputs. `gen_notebooks.py` strips them.

Start a new lab with `uv run --group site python scripts/new_notebook.py mNN`.

## Before you open a pull request

```bash
uv run --group site python scripts/gen_tables.py
uv run --group site python scripts/gen_notebooks.py
uv run --group lint ruff check scripts tests data agents-intro
uv run --group lint ruff format --check scripts tests data agents-intro
uv run --group test python -m unittest discover -s tests -v
uv run --group execute python scripts/test_notebooks.py
quarto render && uv run --group site python scripts/check_links.py
uv run --group browser python scripts/check_browser.py
```

`check_browser.py` opens the rendered site in Chromium at 1280 x 800, 1440 x 900, 1920 x 1080 and 1366 x 768 at 150% zoom, in both themes (desktop only; see AGENTS.md). The first time, install the browser with `uv run --group browser playwright install chromium`.

`uv.lock` pins the environment that local runs and CI use. To move to newer versions, run `uv lock --upgrade`, run the checks above, and commit the lockfile with the fixes it needed; the weekly `drift` leg of `health.yml` shows in advance what an upgrade would break.

To see what stands between `main` and a release, run `uv run --group site python scripts/release_check.py`. Pushing a `v*` tag runs the same check in `.github/workflows/release.yml`, which creates the GitHub Release only if nothing blocks it.

Without flags, `test_notebooks.py` runs each lab's open-model path, which needs the Hugging Face Hub. CI runs the offline test paths instead; the flags are listed in the notebooks job of `.github/workflows/publish.yml`.

Work on a branch and open a pull request against `main`.

## Style

American English. Plain, direct sentences. Define a term the first time it appears. Every equation in a briefing should map to a named step in its lab.

- **Capitalization.** *Title case* for titles and headings: page titles and subtitles, module and day titles, schedule slot names, navigation labels, section, exercise and slide headings, and the titles of callouts ("Text as Data", "Exercise 3 · Temperature Scaling", "Optional: Why the Temperature Fit Is Convex"). *Sentence case* for everything else: prose, objectives, figure captions and alt text, table headers, button labels and bold run-in labels ("**Evidence.**").
  - The rule is APA title case. Capitalize the first word, the first word after a colon, a dash or the middle dot `·`, the last word, and every word of four letters or more. Lowercase the other articles, conjunctions and prepositions: *a, an, the, and, as, but, for, if, nor, or, so, yet, at, by, in, of, off, on, per, to, via, vs.* ("Text as Data", "Skip-Gram With a Full Softmax", "Who It Is For").
  - In a hyphenated word, capitalize every part except a short function word inside it: "Fine-Tuning", "Dot-Product", "Retrieval-Augmented", "Trade-Off", "Human-in-the-Loop", "N-Grams".
  - Keep names, acronyms and symbols as they are spelled: PyTorch, Hugging Face, LangChain, LangGraph, LlamaIndex, LoRA, Jev, TypeSafe, RLHF, Seq2seq, macOS, uv, Recall@k, add-k, version tags such as v1, `code` and $math$. Never use Python's `str.title()` or CSS `text-transform`: they break these.
  - A parenthetical at the end of a heading is a note, not part of the title, and keeps its own case: "(8 minutes)", "(optional)", "(provided)". `scripts/lab_steps.py` reads the minutes from it.
  - Module and day titles live in `_variables.yml`: change them there and rerun both generators. `scripts/titlecase.py` implements the rule; `tests/test_style.py` checks every heading, page title, callout title, notebook heading, navigation label and title in `_variables.yml` with it. A heading's anchor is lowercase, so changing its case does not break links to it.
- **Spelling.** labeled, modeling, normalize, tokenize, behavior, color, center. Keep a British spelling only inside a quotation or the title of a cited work. `tests/test_style.py` flags the common British spellings in published prose.
- **Terms that are easy to confuse.** Say which one you mean.
  - *Checkpoint.* A **checkpoint cell** checks a lab exercise (`workshop.checkpoint(N)`). A **model checkpoint** is saved weights, such as `lab09_reward_model.pt`. A **graph checkpoint** is the state LangGraph saves after each step (Module 14).
  - *Validation set* and *development set* play one role: data for choosing settings, never for the reported number. Use the split's own name: `val` in the Day 1 and 2 datasets, `dev` in the decision set and the question sets, `heldout` in Lab 9's preference data.
  - *Confidence.* Write $\hat{p}$ for a probability that is compared with a threshold or put on a reliability diagram. A model's **stated confidence** is a number it writes in its answer (Module 11). Jev's `confidence` field is $\kappa$, which is not $\hat{p}$ (Module 12, section 8).
  - *Language model (LM).* Spell it out at its first use on a page; "causal LM" and "masked LM" are fine after that. Say whether a loss or a perplexity is per **token**, per **character** or per **word**: numbers over different units cannot be compared.

## License

By contributing you agree that your text is licensed CC BY 4.0 and your code MIT, as described in [LICENSE](LICENSE).
