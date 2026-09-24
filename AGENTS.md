# Working on this repository

Read `HANDOFF.md` and `VALIDATION.md` before changing the experiment. The harness is implemented; equivalence to hosted Luna/ChatGPT has not been established.

- Keep the operator model separate from the experimental decision model (`gpt-5.6-luna`). Never silently substitute models.
- Preserve calibration/validation separation, failed trials, query-versus-action counts, question-cluster repetitions and declared practical margins.
- Never force an open quota or weaken acceptance thresholds to manufacture similarity.
- Raw `results/`, credentials and supplied photos stay local. Public numeric exports belong in `evidence/` and must contain no secrets, private paths or raw API payloads.
- Read `.env` only through the credential loader when an authorized paid run needs it; never print or commit it. Offline tests require no API key.
- Publication does not authorize additional API spending. Ask for a new budget before new paid experiments unless the current user has already explicitly supplied one.
- Run `python3 -m unittest discover -s tests -v` after relevant changes. Preserve corpus/profile/code hashes and create new run directories for changed designs.
- Use `OPUS_RUNBOOK.md` for execution and award-scoring instructions. Public exported metrics are not resumable traces.
