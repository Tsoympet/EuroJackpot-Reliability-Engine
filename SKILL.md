# EuroJackpot Reliability Engine — Cursor Project Skill

## Purpose

This file is the authoritative working instruction set for Cursor or any coding agent modifying the EuroJackpot Reliability Engine repository.

The agent must treat this repository as an auditable probability-research, data-integrity, validation, portfolio-construction, desktop-application, and packaging project. Changes must preserve reproducibility, historical integrity, mathematical correctness, and the distinction between research ranking and true lottery probability.

The project is not a guarantee of winning. Never describe any generated line as mathematically more likely to win than another valid line unless a rigorously validated change to the lottery mechanism itself is established. Under the current 5/50 + 2/12 EuroJackpot rules, each unique valid jackpot line has probability 1 / 139,838,160.

---

## 1. Core operating principles

When asked to update, repair, extend, refactor, test, package, release, or otherwise modify this repository:

1. Inspect the repository before editing.
2. Read `README.md`, `VERSION`, relevant changelogs, affected source files, affected tests/self-tests, and CI configuration.
3. Preserve backward compatibility unless the requested change explicitly requires a breaking change.
4. Prefer minimal, targeted changes over broad rewrites.
5. Never silently delete working functionality.
6. Never fabricate lottery results, prize values, jackpot values, source URLs, verification metadata, performance results, test results, or model metrics.
7. Never overwrite immutable prospective prediction records after the corresponding draw is known.
8. Never train, tune, rank, select, or evaluate a model using information from a future draw relative to the prediction timestamp.
9. Treat all data leakage as a critical defect.
10. Treat mathematically unsupported probability claims as a critical defect.
11. Keep the exact-uniform model available as the fail-safe baseline.
12. Fail closed when verification or validation is insufficient.

---

## 2. Repository truth hierarchy

Use this precedence when determining project truth:

1. Current source code and tests on the checked-out branch.
2. `VERSION` for release version.
3. Canonical history and its source/verification metadata.
4. Current audited model/result artifacts.
5. `README.md` and version-specific documentation.
6. Historical changelogs and archived result artifacts.

If documentation conflicts with executable code, determine which behavior is intentional, fix the inconsistency, and update both code and documentation as needed.

Do not create a second independent version constant when `VERSION` can be used.

---

## 3. Canonical EuroJackpot history rules

The canonical history is a high-integrity dataset and must be handled conservatively.

Before adding a draw:

- Verify the draw date.
- Verify exactly 5 main numbers.
- Verify exactly 2 Euro numbers.
- Validate number ranges for the applicable historical rule era.
- Validate uniqueness within each pool.
- Require at least two reliable independent sources before marking a new draw as verified.
- Prefer official EuroJackpot or participating national lottery operator sources.
- Preserve source names, URLs or source identifiers where the schema supports them.
- Preserve verification status and verification timestamp where supported.
- Do not infer missing prize information.
- Do not replace an unavailable monetary value with zero unless zero is explicitly the true value.
- Use null/blank/unknown according to the existing schema for unavailable values.
- Do not silently rewrite an already verified historical row.

If two reliable sources disagree, stop the update and report the discrepancy. Do not choose one arbitrarily.

When appending history, preserve chronological ordering and existing schema exactly unless a schema migration is intentionally implemented and tested.

---

## 4. Historical rule eras

EuroJackpot rules changed over time. Any logic touching historical draws must use the correct pool sizes and draw-frequency rules for the date being evaluated.

Never apply the current 5/50 + 2/12 rules blindly to all historical records.

Rule-era handling must be centralized where practical and covered by tests. If a rule-era boundary is added or corrected, update all affected validation, probability, training, simulation, and documentation paths.

---

## 5. Draw update workflow

For a normal post-draw update:

1. Verify the official result using at least two reliable sources.
2. Validate the result structurally and against the rule era.
3. Append or update the canonical history only after verification.
4. Preserve verification/source metadata.
5. Score any previously frozen predictions for that draw using the official result.
6. Update adaptive-learning records only from predictions that existed before the draw.
7. Run the relevant self-tests and CI-equivalent checks.
8. Run the audited engine using history only through that draw date.
9. Generate the next-draw research portfolio.
10. Record the exact data cutoff date used.
11. Record engine mode, model/champion status, metrics, and generated artifacts.
12. Explicitly state that generated ranking does not change the mathematical draw probability of a unique valid line.

Never use the just-generated future portfolio as training truth.

---

## 6. Prediction immutability and leakage prevention

Prospective predictions are evidence and must be treated as immutable once frozen.

Do not:

- edit historical predictions after results are known;
- regenerate an old prediction and present it as if it were the original;
- alter prediction timestamps to improve apparent performance;
- tune model parameters on the same future observation used to score them without proper nested or walk-forward separation;
- allow a draw result into features used to predict that draw;
- use future jackpot state, future prize information, or future rollover state in historical simulations.

When a correction to a frozen record is unavoidable because of a software or serialization defect, preserve the original record, create an explicit correction record, document the reason, and keep a complete audit trail.

---

## 7. Statistical and machine-learning governance

The exact-uniform model is the baseline and fail-safe champion unless a challenger clears the repository's predefined evidence gates.

All predictive-edge claims must be based on out-of-sample evidence. Prefer:

- walk-forward evaluation;
- block-prequential evaluation;
- strict train/test chronology;
- calibration analysis;
- Brier/log-loss or other proper scoring rules as appropriate;
- synthetic-null experiments;
- permutation/randomization testing;
- confidence intervals or uncertainty estimates;
- multiple-testing awareness;
- prospective evidence when available.

Never promote a model merely because it fits historical frequencies better in-sample.

If only one number pool demonstrates evidence above the configured threshold, use only that pool-specific research signal where the existing governance permits it. Do not convert a pool-specific ranking signal into a claim that complete jackpot-line probabilities are non-uniform.

If evidence gates fail, fall back to uniform jackpot probability and keep research ranking clearly labeled experimental.

---

## 8. Prize-value and anti-crowd logic

Jackpot size, rollover state, prize caps, lower-prize overflow, estimated popularity, birthday-number concentration, pattern avoidance, and anti-crowd heuristics may affect expected prize-sharing or portfolio utility.

They do not change the physical probability that a valid unique line is drawn.

Keep these concepts separate in naming, UI labels, JSON output, reports, tests, and documentation:

- draw probability;
- model research score;
- portfolio utility;
- coverage;
- estimated prize-sharing exposure;
- expected value assumptions.

Never label a prize-value or anti-crowd score as a draw probability.

---

## 9. Engine modes

Preserve the intended distinction between modes such as audited and full/research execution.

`audited` mode should use the latest accepted/audited artifacts and remain suitable for routine operation.

`full` or research modes may execute computationally expensive training/search procedures but must not silently promote a challenger without passing governance gates.

Every generated prediction report should include, where available:

- engine version;
- engine mode;
- run timestamp;
- data cutoff date;
- history row count;
- champion/deployment decision;
- primary line;
- diversified portfolio lines;
- relevant evaluation metrics;
- verification/data provenance summary;
- probability disclaimer.

---

## 10. Adaptive learning

Adaptive learning may re-rank experimental portfolios but must not be allowed to rewrite lottery mathematics.

For post-draw scoring, use `eurojackpot_post_draw.py` or the repository's current supported equivalent.

A result may be learned from only if the prediction being scored was frozen before the draw result became available.

Maintain a clear separation between:

- training state;
- live/frozen predictions;
- post-draw scoring;
- evaluation metrics;
- deployment/champion governance.

Self-tests for adaptive learning must remain deterministic where practical.

---

## 11. Coverage wheels

Treat verified wheel files as mathematical artifacts.

Do not modify pair/triple wheel content casually. Any change to a wheel must be independently verified against its claimed coverage property and expected line count.

Preserve existing CI line-count checks unless the wheel specification intentionally changes.

If a wheel changes, add or update independent verification tests and documentation.

---

## 12. Desktop application

Changes to `eurojackpot_desktop_app_v3_8.py` or its successor must preserve:

- ability to generate predictions;
- visibility of engine/audit status;
- learning functions;
- stable-edge research functions;
- history/data handling;
- ticket rendering;
- user-data directory behavior;
- cross-platform compatibility where supported.

Long-running work must not freeze the GUI if the current architecture already performs it asynchronously.

Errors shown to users must be actionable and must not expose secrets or misleading success states.

---

## 13. Paths and user data

Use `eurojackpot_paths.py` and existing path helpers instead of scattering platform-specific paths through the codebase.

Respect `EUROJACKPOT_DATA_DIR` for CI, portable, and isolated runs.

Do not write runtime outputs into the installation directory when the project design expects per-user data directories.

Do not commit transient user-specific runtime files, local caches, secrets, virtual environments, or generated build directories unless they are intentional release artifacts already tracked by project convention.

---

## 14. Testing requirements

Before considering a code change complete, run the narrowest relevant tests and then the practical CI-equivalent suite.

At minimum, preserve compatibility with the checks in `.github/workflows/ci.yml`, including as applicable:

```bash
python run_eurojackpot_jackpot_state_selftest_v3_5.py
python eurojackpot_independent_verifier_v3_4.py --root .
python eurojackpot_one_click_v3_7.py --engine-mode audited --db EuroJackpot_CI.sqlite --output-dir outputs
python run_eurojackpot_ticket_render_v3_6.py
python run_eurojackpot_learning_selftest_v3_8.py
python eurojackpot_learning_engine_v3_8.py train-history --db history.sqlite --min-history 80 --max-draws 40
python eurojackpot_edge_engine_v3_8.py selftest
```

Also compile Python files after modifications:

```bash
python -m compileall .
```

Use the repository's pinned dependencies from `requirements.txt`.

Never claim tests passed unless they were actually executed successfully in the current environment. If a test cannot run because of environment limitations, report that explicitly.

---

## 15. CI integrity

Do not weaken CI merely to make a failing change pass.

Do not remove:

- file-format integrity checks;
- JSON parsing checks;
- SQLite usability checks;
- wheel row-count checks;
- dependency pin checks;
- compilation checks;
- independent verifier execution;
- learning self-tests;
- stable-edge self-tests;

unless the underlying requirement is intentionally replaced with an equal or stronger validation mechanism.

When changing file names or versions, update CI paths atomically.

---

## 16. Versioning and release updates

`VERSION` is the single release-version source of truth unless the architecture is intentionally changed.

For a release/version bump:

1. Update `VERSION`.
2. Update version-specific documentation/changelog.
3. Update packaging metadata that cannot read `VERSION` dynamically.
4. Update Windows PyInstaller/Inno Setup references where necessary.
5. Update Linux/Debian packaging metadata where necessary.
6. Update launch scripts if entrypoint names change.
7. Update README commands and displayed version.
8. Run CI-equivalent tests.
9. Build packages only after source tests pass.
10. Record known limitations and statistical conclusion.

Do not rename every file solely to match a version number unless that is already the project's deliberate versioning convention and the change is requested.

---

## 17. Windows packaging

When touching Windows packaging, inspect and keep synchronized as applicable:

- `EuroJackpotEngine_v3_8.spec`;
- `EuroJackpotEngine_v3_8.iss`;
- `Build_Windows_Installer.ps1`;
- `Install_EuroJackpot_Windows.ps1`;
- launcher `.bat` / `.cmd` files;
- icons and ticket-template assets.

Verify resource paths work both from source and from a frozen executable.

Do not assume development-machine absolute paths.

---

## 18. Linux packaging

When touching Linux packaging:

- preserve executable permissions where required;
- keep package version synchronized with `VERSION`;
- verify desktop-entry/icon paths if present;
- verify installed launchers resolve packaged Python/resources correctly;
- avoid writing runtime state into system package directories.

Test source execution separately from installed-package behavior.

---

## 19. Ticket-image generation

Prediction-ticket rendering must use the exact numbers from the corresponding generated prediction artifact.

Never allow display order, formatting, image generation, or OCR-like transformations to change the selected numbers.

After renderer changes, run the ticket render smoke test and validate that rendered payloads correspond exactly to source prediction data.

---

## 20. Database changes

SQLite schema changes require explicit migration handling.

Do not destructively recreate an operational user database just to apply a schema update.

For schema changes:

- inspect existing schema/version markers;
- add forward migration logic;
- make migration idempotent where practical;
- preserve existing runs, predictions, scoring, learning, audit, and artifact records;
- test migration from at least one representative prior schema;
- use transactions;
- create backups where the existing architecture supports them.

Never insert fabricated historical runs to satisfy a schema expectation.

---

## 21. Security and secrets

Do not hard-code credentials, tokens, passwords, private API keys, or private endpoints.

Use environment variables or the repository's existing secure configuration approach.

Do not commit `.env` files containing secrets.

Treat fetched external data as untrusted input. Validate formats, ranges, dates, and types before storing or using it.

Network failures must not cause unverified fallback data to be treated as official.

---

## 22. External-source verification

When online access is available and the task depends on current EuroJackpot data:

1. Prefer official EuroJackpot/national lottery operator sources.
2. Require two reliable sources before final verification of winning numbers.
3. Record retrieval date/time if the data model supports it.
4. Distinguish official result data from secondary reporting.
5. Do not scrape around explicit access controls.
6. Do not treat search snippets alone as sufficient proof when the underlying source can be checked.
7. If verification cannot be completed, leave the draw unverified and stop downstream official-result ingestion.

Prize values may be published later than winning numbers. Do not delay number verification solely because prize tables are unavailable, but represent unavailable prize fields honestly.

---

## 23. Coding standards

Follow the style already present in the repository.

Prefer:

- Python type hints for new public interfaces;
- deterministic pure functions for statistical logic;
- small functions with explicit inputs/outputs;
- `pathlib.Path` for paths;
- structured JSON/SQLite records for auditable outputs;
- clear exception messages;
- seeded randomness in tests and reproducible research runs where applicable;
- comments explaining why, not obvious syntax.

Avoid unnecessary dependencies. If a new dependency is required, justify it, pin it consistently with project policy, and update CI/package configuration.

---

## 24. Refactoring rules

Before refactoring shared probability or history code, identify all callers.

Preserve numerical behavior unless the refactor intentionally corrects a documented defect.

For numerical corrections, add regression tests demonstrating the prior failure and the corrected expected behavior.

Do not combine an unrelated refactor, data update, model change, and release bump into one opaque change if they can be separated cleanly.

---

## 25. Documentation rules

Update documentation whenever user-visible behavior, commands, file names, model governance, data sources, or packaging changes.

Documentation must never imply guaranteed predictive power.

Always distinguish:

- mathematically exact jackpot odds;
- historical statistical observations;
- research-model scores;
- experimental edge evidence;
- prize-value/anti-crowd optimization;
- coverage gained by buying multiple unique lines.

When reporting a model improvement, state the evaluation design and baseline.

---

## 26. Change log discipline

For material changes, add an entry to the relevant changelog or create the next-version changelog if a version bump is intentional.

A changelog entry should identify:

- what changed;
- why it changed;
- affected files/components;
- compatibility impact;
- validation performed;
- any migration requirement;
- statistical/governance impact where relevant.

Do not record a test as passed if it was not executed.

---

## 27. Git workflow

Unless explicitly instructed otherwise:

- work on a focused branch for substantial changes;
- keep commits logically scoped;
- use descriptive commit messages;
- do not force-push shared branches;
- do not rewrite unrelated history;
- do not merge with failing required checks;
- review the final diff for accidental generated files, credentials, or data corruption.

For a simple documentation-only correction, a direct commit may be acceptable if repository policy permits it.

Suggested branch patterns:

```text
fix/<short-description>
feature/<short-description>
data/update-eurojackpot-YYYY-MM
release/vX.Y.Z
```

---

## 28. Definition of done

A task is complete only when all applicable conditions are satisfied:

- requested functionality is implemented;
- historical integrity is preserved;
- no future-data leakage is introduced;
- exact-uniform probability safeguards remain correct;
- relevant tests pass;
- CI configuration remains valid;
- documentation is synchronized;
- version/package files are synchronized if relevant;
- generated output is reproducible where expected;
- no secrets or local-machine paths are committed;
- the final diff has been reviewed;
- limitations or unexecuted validation steps are explicitly reported.

---

## 29. Standard final report from Cursor

After completing a task, report concisely:

```text
Task:
Files changed:
Data cutoff (if applicable):
Draw verification sources (if applicable):
Engine mode (if applicable):
Tests executed:
Tests passed/failed:
Artifacts generated:
Version change:
Migration required:
Known limitations:
Probability statement: All valid unique EuroJackpot combinations retain the same mathematical draw probability under the applicable lottery rules.
```

Do not invent any field. Use `N/A` when it truly does not apply.

---

## 30. Priority instruction

When requirements conflict, prioritize in this order:

1. mathematical correctness;
2. historical and prospective-data integrity;
3. reproducibility and auditability;
4. user data safety;
5. test/CI integrity;
6. compatibility;
7. requested feature behavior;
8. performance;
9. cosmetic improvements.

If a requested implementation would violate items 1–5, do not implement it silently. Implement the safest valid alternative and explain the conflict.
