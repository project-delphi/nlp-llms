# Pilot Protocol

**Status (2026-10-08): prepared, not run.** No pilot has taken place. Running one needs participants and a facilitator; nothing in this folder is a result until a session has been held and recorded.

A notebook that runs top to bottom is not yet a lab that fits its slot. `runs/` records how long the computer takes. The pilot measures how long people take, where they stall and which explanations do not land, so that each core path can be cut or rebalanced before the first delivery.

## Who Takes Part

- **Three to six participants** who match the workshop's stated prerequisites: they take the entry check on `prepare.qmd` and miss fewer than two questions in every area (Python, NumPy, machine-learning basics, PyTorch, mathematics). Anyone who wrote or reviewed the labs is not a participant.
- **One observer for every two or three participants.** The observer watches, times and writes; the observer does not teach. Help only after five minutes without progress, and record that you helped.
- Each participant uses their own laptop and a fresh free-tier Colab runtime, with no API keys set: the path most participants will take. Record the runtime type (T4 or CPU) on every row.

## What to Pilot First

Start with the known risks, in this order:

1. **The exercises that rely on a Reference section**, which is not taught in the room: Lab 1, Exercise 6 (Module 1, section 6, precision, recall and F1); Lab 3, Exercise 5 (Module 3, section 7, sampling); Lab 9, Exercise 1 (Module 9, section 5, generation as sequential decisions). Each exercise restates what it needs. The question is whether that is enough.
2. **The dense later system labs, 13 to 15**: many provided cells, long-running steps, and evaluation tables to read before the explanation questions.

Run each piloted module as it will be taught: the briefing to its live plan, then the lab in its slot (a 50-minute core path; on Days 2 to 5, 55 minutes including 5 of slack for setup and downloads), then the debrief. Do not let the debrief absorb unfinished lab work.

## What to Record

Copy `observations_TEMPLATE.csv` to `observations_<date>_<session>.csv`, delete its two example rows, and write one row per participant per exercise. For each exercise:

- **Clock times.** `start` when the participant first reads the exercise heading, `end` when its checkpoint cell passes or they move on. Use the wall clock (HH:MM), not the notebook's timers.
- **Help used.** Whether they opened a folded hint, where the exercise has one (`hint_used`: `yes`, `no` or `none` if there is no hint), and whether they read the folded solution or called `workshop.use_reference(N)` (`reference_used`: `no`, `read-solution` or `use_reference`). Help from the observer goes in `notes`.
- **The checkpoint.** `passed-own`, `passed-reference`, `failed` or `not-reached`, as the checkpoint cell reports it.
- **Where they stalled.** The cell or step, and for about how long.
- **What was unclear.** The briefing section or notebook sentence they could not use, in a few words.

Also record **setup delays** as a row with `exercise` set to `setup`: from opening the Colab link to the first exercise cell running (harness, setup and data cells, downloads, runtime changes). Note anything that blocked the whole room, such as a failed download, in `notes`.

## Keep Observations Apart From Run Records

- **Compute timing stays in `runs/`.** When a notebook finishes, its last code cell prints a run record; add it with `scripts/add_run_record.py`, giving the real environment. That is the only source of run times and "has run on" claims on the site.
- **Facilitation observations stay in this folder.** Participant minutes, help used and stalls are never added to `runs/`, never quoted as a Colab, T4 or compute time, and never typed into a page as a run time.
- A CPU or laptop time is never labeled a Colab or T4 time, in either place.

## Privacy

- **No names.** Participants are `P1` to `P6` and observers `O1`, `O2`, … within a session. Keep the list that maps codes to people off the repository, and delete it when the pilot is analyzed.
- **No identifying details**: no email addresses, Colab account names, screenshots of people or screens with accounts on them.
- **No secrets.** If a key appears on a screen or in a notebook, follow the facilitator guide (delete it, rotate it); never write it down.
- Notes describe the material, not the person: "the Explain prompt after Checkpoint 6 did not say which averaging to use", not "P3 was slow".
- Ask each participant's agreement before the session, and tell them what is recorded and where.

## How Results Feed Decisions

For each exercise, compare the median and the slowest participant's minutes with the minutes in the exercise heading, and count how many needed the hint or the reference. Then decide:

- **An exercise runs long, or most participants need the reference**: simplify its scaffold, add a focused hint, or move part of it to the lab's single stretch section. Do not add a second stretch section.
- **A Reference-section exercise stalls**: move the minimum explanation into the module's live plan, and keep the briefing within its minutes by moving another topic to Reference.
- **Setup delays exceed the slack** (5 minutes on Days 2 to 5, none on Day 1): fix the setup or data cells first; they cost every participant.
- **A core path fits its slot** only when the participants finish all core exercises, including the written Explain answers, within the 50 minutes, with time left to interpret the results. A run that merely completes does not count.

Record each decision and its evidence (the session file and the rows) in `PLAN.md`, change the content through its usual source (module page, notebook, `_variables.yml`), and pilot the changed module again.
