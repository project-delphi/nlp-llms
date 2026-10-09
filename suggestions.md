# Suggestions for Clearer Workshop Materials

Reviewed on October 8, 2026. These are recommendations from a source review, not implemented changes. Priorities reflect likely value to participants and instructors, not measured learning outcomes.

The workshop already has a strong foundation: objectives, recaps, worked numeric examples, Predict → Run → Explain → Check exercises, folded solutions, equation-to-lab maps, daily retrieval practice, and run records. Improve their consistency and connections before adding more content or more platforms.

## Address First

### 1. Establish and Apply a Capitalization Convention

- [x] Use **title case for page titles, module titles, navigation labels, and section/exercise headings**, and sentence case for prose, objectives, captions, and explanatory labels. Document this in [CONTRIBUTING.md](CONTRIBUTING.md).

**Evidence:** [_variables.yml](_variables.yml) currently uses titles such as “Text as data,” “Word vectors and neural networks,” and “Pretraining and the Hugging Face stack.” [teach.qmd](teach.qmd) uses “Teach this workshop.” There is no explicit casing rule in the contributor guide. Sentence case is a valid convention; the gap is the missing policy, rather than every lowercase word being an error.

**Suggested examples:** “Text as Data,” “Word Vectors and Neural Networks,” “Pretraining and the Hugging Face Stack,” “Teach This Workshop,” and “Scaled Dot-Product Attention.” Choose one rule for hyphenated headings, such as “Fine-Tuning and LoRA” and “Retrieval-Augmented Generation.” Preserve spellings such as PyTorch, Hugging Face, LangGraph, LoRA, and Jev.

Change canonical module/day titles in `_variables.yml`, then rerun both generators. Update handwritten headings separately. Do not apply Python's `str.title()` or CSS `text-transform` indiscriminately: these can damage acronyms or conceal inconsistent source text. Preserve explicit anchors and check existing heading links after renaming.

**Completion check:** the same module has the same title on its page, notebook, schedule, sidebar, and reference entry; generated files remain reproducible.

**Done, October 8, 2026, with a different choice:** CONTRIBUTING.md now records **sentence case** for every title and heading, not title case. Sentence case is already applied consistently across `_variables.yml`, every heading and the navigation. The one title-case string is the workshop's name, which the rule exempts as a name. Switching to title case remains a one-file change in `_variables.yml` plus a heading pass.

### 2. Correct Contradictory Learner Instructions and Stale Status Text

- [x] Audit participant-facing setup, prerequisite, and readiness statements against the current sources.

**Evidence:** [notebooks.qmd](notebooks.qmd) says Lab 9's preference data and reward model are “not built yet,” although `data/lab09_preferences.jsonl.gz` and `data/lab09_reward_model.pt` are present and their creation is recorded in [PLAN.md](PLAN.md), Phase 6. Its layout list also says both the setup cell and the harness cell should be run first.

State one sequence: **harness → setup → data → exercises**. Explain learner mode, worked-example mode, and `workshop.use_reference(N)` beside that sequence. Separate independent execution from optional cross-lab comparisons that require an exported artifact. Describe prerequisites concretely and obtain changing readiness claims through the existing readiness machinery.

Also update [CONTRIBUTING.md](CONTRIBUTING.md): its editing table excludes only the first and last notebook cells, while [AGENTS.md](AGENTS.md) and the generators protect four cells, including the harness and summary.

**Why it helps:** participants can distinguish an unfinished exercise from a setup failure, and contributors can avoid editing generated content.

**Done, October 8, 2026:** `notebooks.qmd` gives the run order harness → setup → data → exercises, names learner and worked-example modes, and explains the three checkpoint messages and `workshop.use_reference(N)`. It names the one cross-lab file, Lab 11's optional export for Lab 12. CONTRIBUTING.md lists the four generated cells.

### 3. Finish the Missing System Diagrams

- [x] Turn the existing figure specifications into visible, captioned diagrams, starting with Modules 12–15.

**Evidence:** comments specify `images/12-route-guard-verify.svg`, `images/13-rag-pipeline.svg`, `images/14-desk-agent-graph.svg`, and `images/15-capstone-graph.svg`; those files are absent from `images/`. Modules 9–11 also contain unfinished figure specifications. These comments do not display diagrams to learners. Some concepts already have interactive demos, so inspect those before creating duplicate plots.

Draw the RAG pipeline with separate indexing and query lanes. Draw the agent graph with conditional edges, the human interrupt, termination, and the guard before the risky tool. Match node names to the lab's code and identify which exercise changes each component. Use the existing SVG style or Mermaid for control-flow diagrams; generate numeric plots from code or recorded data. Include alt text and verify desktop readability in both themes.

**Why it helps:** learners can see the whole system while reading about individual stages. Start with the missing architectural diagrams rather than decorative images.

**Done, October 8, 2026:** all 13 specified figures for Modules 9–15 are drawn and captioned. Where a spec disagreed with the lab code, the figure follows the code.

### 4. Resolve the Core-Lab Versus Reference-Reading Mismatch

- [x] Make essential lab prerequisites part of the live explanation or provide an explicit short refresher immediately before the exercise.

**Evidence:** Module 1's precision/recall/F1 section and Module 3's sampling section are marked `.reference`, although core lab exercises use them. [PLAN.md](PLAN.md), Phase 4, already identifies this as something to watch in the pilot.

For each objective, review the chain **briefing section → exercise → checkpoint → knowledge check**. Where a core exercise depends on reference material, either promote the minimum explanation into the live plan or link a focused refresher from the exercise. Keep the timing budget unchanged by removing or postponing another topic.

**Completion check:** a participant following only the scheduled briefing and core lab receives the definitions and reasoning needed for every required exercise.

**Done, October 8, 2026, without changing the timing:** three core exercises use a Reference section: Lab 1 Exercise 6, Lab 3 Exercise 5 and Lab 9 Exercise 1. Each already restates the definitions it needs. The generated agenda now says so instead of only "read them after the session", and each of those sections opens with a pointer to its exercise. The pilot (suggestion 13) should still check that this is enough.

### 5. Standardize American English and Technical Vocabulary

- [x] Add a short terminology/style guide and perform a targeted editorial pass.

**Evidence:** published text in Modules 11–14 includes “labelled” and “human-labelled,” despite the American English rule in [AGENTS.md](AGENTS.md). Module 13 uses “labelled evidence” in its retrieval objective. Use “labeled” and “human-labeled” in authored prose.

Choose consistent terms for validation/development sets, language model/LM, token/character, confidence/probability, and checkpoint. Define distinctions rather than collapsing them: a learner checkpoint checks an exercise; an agent checkpoint stores execution state. Jev's `confidence` field and the probability used in a decision threshold also need separate explanations.

Add a small allowlisted prose check for known spelling variants and product names. Exclude source code, model IDs, URLs, literal API fields, quotations, and generated content; check their authoring sources instead.

**Done, October 8, 2026:** published sources use "labeled" and "center". Data artifacts and their build scripts are unchanged, because their text is hashed. `tests/test_style.py` guards the spelling. CONTRIBUTING.md defines the confusable terms: checkpoint cell, model checkpoint and graph checkpoint; `val`/`dev`/`heldout`; $\hat{p}$, stated confidence and Jev's $\kappa$; units of perplexity. Module 14 now says "checkpoint cell" where it means the lab's checks. Product names are not checked by the test.

## Strengthen Conceptual Understanding Next

### 6. Add a Shared Glossary and Notation Index

- [ ] Provide a compact learner reference, linked from relevant first uses and the References page.

Several later modules already have local notation tables. Connect these rather than repeating full definitions everywhere. For each term or symbol, give a plain definition, its first module, a small example, and a link to the implementing exercise. Keep scalar/vector/matrix distinctions and tensor dimensions explicit.

Useful entries include token, logit, embedding, context window, cross-entropy, perplexity, reward, calibration, abstention, retrieval, reranking, state, and interrupt. Explain reused symbols locally: Module 5 uses `V` for the value matrix, while language-model discussions use vocabulary notation.

**Completion check:** a learner returning to a module can recover a term's meaning and its code counterpart without searching several briefings.

### 7. Make the Live Reading Path Easier to Scan

- [ ] Extend the existing agenda and Reference badges with a concise “Read now / Use in the lab / Read later” guide.

The module pages are substantial reference documents, and the repo already separates some reference sections from scheduled teaching. Make that separation visible near the agenda and in links to exercises. Keep the full explanation available; do not simply shorten away the derivations.

For a dense section, lead with the question being answered and one concrete example, then show the minimum derivation. Label extra derivation or framework detail as optional. Drive live coverage from the existing `live:` front matter to avoid a second schedule.

**Why it helps:** participants know what to focus on during a timed session and what to revisit afterward.

### 8. Add Compact Comparisons Where Concepts Are Easily Confused

- [ ] Add comparison tables at the relevant transitions, reusing existing explanations.

| Transition | Distinction to make explicit | Learner prompt |
|---|---|---|
| Modules 4 → 5 | Cross-attention versus self-attention; recurrence versus parallel training | Where do the queries, keys, and values come from? |
| Modules 6 → 7 | Pretraining versus fine-tuning; full updates versus LoRA | Which weights change, and which loss is optimized? |
| Modules 9 → 10 | Reward-model fitting versus policy optimization versus DPO | Which object is learned from which data? |
| Modules 11 → 12 | Accuracy versus calibration versus decision cost | Can the most accurate model be the worse decision system? |
| Modules 13 → 14 | Retrieval pipeline versus agent control loop | What chooses the next action, and what stops the loop? |

Use columns such as input, output, objective, updated parameters/state, and typical failure. Ask learners to explain the distinction on a new example. For RLCD, preserve the separation between TypeSafe's public statements and the workshop's toy illustration; do not invent an algorithm comparison.

### 9. Link Checkpoint Failures to Specific Misconceptions

- [ ] Review assertion messages and add one optional hint before the full solution where a learner is likely to stall.

The labs already test stubs, provide solutions, and report whose code passed. Extend that structure with messages that show the observed versus expected value and the likely issue. Examples: normalize attention across keys, exclude future positions, fit preprocessing on training data, or divide a metric by the correct denominator.

Add a minimal counterexample for common wrong implementations. A hint should identify the principle or relevant briefing section without supplying the entire function. Make hints foldable so learners can choose when to use them.

**Completion check:** a failed checkpoint tells a participant what to inspect next. Correct outputs still require the participant to explain why the method works.

### 10. Turn the Running Results Table Into a Reusable Learner Artifact

- [ ] Provide a small worksheet or exportable template based on the tables already used in the day wrap-ups.

Record task, dataset/split, tokenization unit, model, baseline, metric and direction, seed, runtime/path, result, and one interpretation. Keep language modeling, classification, instruction following, and system evaluation in separate comparison groups.

[day-2.qmd](day-2.qmd) already asks why Lab 7's perplexity cannot share a comparison column with Lab 5's. Build on that: place comparison conditions beside each result, and leave participant results blank until measured. Any published run-time or verification claim must continue to come from `runs/` through the existing generators.

**Why it helps:** learners leave with evidence of what changed and can recognize when two scores do not support a fair comparison.

### 11. Add Short Transfer Tasks to the Existing Checks

- [ ] Supplement selected checks with a new example that tests reasoning beyond the implementation fixture.

The workshop already has knowledge checks, folded answers, and spaced warm-ups. Use those slots rather than adding another quiz platform. Examples: predict how a changed tokenization affects perplexity comparisons; diagnose high retrieval recall with poor answer correctness; choose an action after the cost of error changes; explain why replay should not send an email twice.

Pair an answer with the misconception it rules out and the lab exercise to revisit. Keep these within scheduled activity/debrief time. A passing reference solution demonstrates code execution; a correct explanation on a changed example provides different evidence of understanding.

### 12. Make Runtime and Fallback Differences Visible at the Result

- [ ] Use the existing readiness/path terminology consistently in result tables and notebook summaries.

The repo already distinguishes offline test doubles, real open models, commercial API paths, and the toy decision model. Show the active backend beside the result, plus what that result can establish. Keep scripted control-flow checks separate from model-quality measurements.

Prioritize completing the already-planned human question sets, decision audits, and fresh Colab runs before claiming those evaluation labs are ready. Do not replace independent human labels with generated labels. Reuse the existing readiness items and release checks instead of creating another status list.

**Why it helps:** participants understand whether they measured a real model, illustrated a mechanism, or checked software behavior.

### 13. Validate the Teaching Pace With Learners

- [ ] Run a short pilot that measures participant work, not just notebook execution.

The exercise headings already allocate time, and the live plans account for briefing activities. Record setup delays, time to complete each exercise, where hints or reference solutions were needed, and which explanations remained unclear. Start with the known Module 1/3 reference mismatch and the dense later system labs.

Use observations to cut scope or move material to the single stretch section. Keep compute timing in `runs/`; record facilitation observations separately so a CPU execution time is never presented as a Colab or learner-completion time.

**Completion check:** the core path fits its teaching slot with time for interpretation, not merely successful execution.

## Suggested Order of Work

1. Set the casing/style rule; correct the stale notebook instructions and generated-cell guidance.
2. Complete the missing RAG, decision-system, and agent diagrams; resolve required concepts labeled Reference.
3. Add the glossary, transition comparisons, and focused checkpoint hints.
4. Reuse the day results tables and knowledge checks for learner records and transfer tasks.
5. Complete existing readiness work and pilot the revised core paths before expanding scope.

For implementation, edit handwritten sources and canonical variables, regenerate owned content, check generator drift and links, and render the site. Execute notebook changes in the modes required by `AGENTS.md`. Review heading/diagram changes in current desktop browsers, both themes, and the existing desktop zoom checks. Mobile work remains outside this repository's scope.

## Review Scope

Reviewed `PLAN.md`, `AGENTS.md`, contributor guidance, root learning/setup pages, module headings and selected explanations, knowledge checks, image inventory/specifications, and representative notebooks (01, 05, 11, 13, and 14). Inspected the relevant generator, lab-step, live-plan, and harness sources. This was a source review: no notebook execution, Quarto render, browser inspection, or live SDK verification was performed. No API changes or current pricing recommendations are proposed.
