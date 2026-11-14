# IntelSphere AI — working local project

Built for Vaibhav Singh's AI product and business-analysis portfolio.

## Open it now

1. Extract the ZIP.
2. Double-click **IntelSphere_Working.html**.
3. The sentiment model and the complete review-to-roadmap workflow run in your browser. No installation or API key is needed.
4. Click **Save workspace** to save on this device, or Export → JSON backup.

If your browser blocks storage for local HTML files, use JSON exports or the Python server below. The app shows storage errors; it does not claim a save succeeded when it failed.

## Run with local SQLite storage

Requires Python 3.10 or newer. No pip packages are needed.

From the extracted folder:

    python server.py

Open http://127.0.0.1:8766 in your browser. Keep the terminal open. Stop with Ctrl+C.

The database is runtime-data/intelsphere.sqlite3. It stays on your computer. The server listens only on 127.0.0.1. Save explicitly after changes.

## A five-minute walkthrough

1. Overview: inspect the 36 synthetic reviews and the calculated sentiment/theme charts.
2. Review explorer: open a review, inspect the model label, and record a human correction.
3. Data sources: download the CSV template or import your own permitted feedback.
4. Feature opportunities: open an opportunity and inspect the actual supporting reviews.
5. Change the impact score, analyst confidence, or effort. Inspect the updated RICE score.
6. Add a discovery brief to Roadmap & PRD.
7. Open the draft, edit its scope and acceptance criteria, assign an owner, and save.
8. Export the Markdown PRD, selected review CSV, or full JSON backup.

Use filters to inspect one competitor, platform, date range, or data origin. The overview, review table, themes, opportunities, and executive report all use the same selected cohort. Roadmap briefs retain the cohort from the time they were created.

## What actually works

- CSV and JSON review imports, with row-level validation and duplicate reporting.
- Local machine-learning sentiment inference: Positive, Neutral, Negative, or Uncertain.
- Human sentiment corrections that preserve the original prediction.
- Rule-based feedback themes and explicit switch-intent phrase detection.
- Data-derived metrics, charts, theme comparisons, and cohort filtering.
- Evidence-linked opportunities and editable RICE assumptions.
- Editable discovery PRDs with original review citations.
- Saved roadmap snapshots that flag changed evidence or scoring.
- Markdown/CSV/JSON exports and backup restoration.
- Browser-local storage or a standard-library Python/SQLite server.

## What AI means here

The classifier is a trained **multinomial Naive Bayes** model. It learns token frequencies from 60 original synthetic English examples, 20 per sentiment class. It uses unigram/bigram features and add-one smoothing. It performs inference on your text locally.

It is a small experimental model, not an LLM. It can misclassify unfamiliar vocabulary, negation, mixed feedback, sarcasm, and multilingual text. Uncertain results are retained. Internal class scores are not calibrated probabilities.

Themes, concern detection, switch-intent phrases, RICE arithmetic, and PRD templates use deterministic code. They are labeled separately from sentiment ML.

No provider account, key, or network connection is required for analysis. No live scraping or external LLM call is implemented in this version.

## Evidence and calculation rules

- Net sentiment = 100 × (positive − negative) / classified reviews.
- Classified means Positive, Neutral, or Negative. Uncertain is excluded from that denominator.
- Theme mentions can overlap; they do not have to sum to the total number of reviews.
- Switch-intent signals are explicit phrases, not predicted churn probabilities.
- An opportunity needs matching feedback with a negative label, explicit concern, feature request, or switch-intent signal.
- RICE = reach × impact × confidence / effort.
- Reach is a supporting-review-count proxy for this cohort, not market reach.
- Impact, confidence, and effort are analyst assumptions. RICE confidence is not a sentiment-model probability.
- A PRD cites up to 20 evidence examples and records all supporting review IDs.
- Reported feedback does not establish that a competitor lacks a feature.

## Data format and limits

Required fields: text and competitor. A default competitor can be supplied in the import dialog.

Optional: platform, rating, date, source_id, url, origin.

- Rating: an integer 1–5 or blank.
- Date: YYYY-MM-DD or blank; undated rows are excluded when date bounds are active.
- URL: HTTP/HTTPS only.
- origin=Synthetic preserves synthetic provenance. Otherwise imported records are labeled Imported.
- Max import: 500 rows, file under 2 MB.
- Max workspace: 1,500 reviews and 30 roadmap drafts.
- Max review length: 5,000 characters.
- Max save/restore: approximately 8 MB.
- Duplicate text within the same competitor and platform is skipped.
- Source ID collisions with different text are reported instead of overwritten.

## Model diagnostic and tests

34 automated checks cover core behavior, import validation, UI handlers, local API persistence, and the standalone package. UI handler tests use a document stub; they are not real browser tests.

A separate diagnostic uses 18 developer-authored synthetic examples. See docs/LOCAL_MODEL_DIAGNOSTIC.md for the actual results and limitations. It is not a representative real-world accuracy benchmark.

Run checks with Node.js 20+ and Python 3.10+:

    node --test tests/engine.test.mjs tests/ui.test.mjs tests/demo.test.mjs
    python -m unittest discover -s tests -p test_server.py -v

Regenerate the package's static assets:

    node scripts/build.mjs

Regenerate the synthetic diagnostic:

    node scripts/evaluate.mjs

## Project map

| Path | Purpose |
| --- | --- |
| IntelSphere_Working.html | Self-contained application; no external assets |
| web/engine.js | Local model, imports, metrics, opportunities, RICE, PRDs |
| web/app.js | Interface and review workflow |
| web/style.css | Responsive dashboard styling |
| server.py | Local SQLite API |
| examples/ | Synthetic review data, training examples, diagnostic cases/results |
| docs/PROJECT_GUIDE.md | Business and AI learning guide |
| docs/VALIDATION.md | Passed checks and remaining verification |
| scripts/build.mjs | Standalone/static build |
| .openai/hosting.json | Existing private Site identity for future publication |

## Hosting status

A private Site was registered. Source synchronization failed because the environment could not resolve/connect to its Git host. No deployment was completed and no live Site URL is claimed. The local app does not depend on hosting.

The buildless static assets are in dist after running the build script. Continue publication against the existing project ID in .openai/hosting.json; do not create a duplicate Site.

A hosted static deployment uses device-local browser storage. The Python/SQLite service is a separate local mode, not a deployed backend.

## Portfolio positioning

This is an implemented local AI product prototype with evidence-backed product discovery. It is suitable for a walkthrough and honest in-progress portfolio case study.

Do not claim real-time scraping, GPT integration, 1,000 weekly reviews, an 85% time reduction, production adoption, or real-world model accuracy without separately verified evidence.


