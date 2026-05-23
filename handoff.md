# Handoff — NEET PYQ Quiz

## Goal

A self-hosted NEET exam prep app for personal use. The end state is:
- All NEET PYQ (2016–2024) and 9 mock tests in a single question bank
- A clean quiz UI with configurable filters, timer, mock-test mode
- Attempt history saved locally + to Supabase
- PDF report download and email report after each quiz
- Deployed on Vercel at the existing URL

The quality bar: every question should be legible (including image questions and match-the-column tables), scores should calculate correctly, and the data should be clean (correct subjects, no orphaned images, no duplicate IDs).

---

## Current State

### Data (`public/questions.json`)
- **3494 questions** total: 1880 PYQ (`source: "neet_pyq"`) + 1614 mock (`source: "mock"`)
- **977 questions** have `has_image: true` with a valid `image_path`; images live in `public/images/`
- **8 questions** have `correct_answer: null` (NTA-canceled; shown with a warning banner, excluded from scoring)
- All questions have `source` backfilled; `has_image`/`image_path` backfilled for the 299 that had path-only issues
- ~15 PNGs in `public/images/` are probe/debug files from extraction (`del_mid5x.png`, `probe_page7.png`, etc.) — they are genuinely orphaned and can be deleted manually

### App structure
```
src/
  App.jsx                      — routes + provider tree
  context/
    QuestionsContext.jsx        — async fetch + computeMetadata; provides { questions, metadata, loading, error }
    QuizContext.jsx             — quiz session state (START_QUIZ, ANSWER, FINISH)
  pages/
    Home.jsx                   — stats + recent attempts
    Config.jsx                 — filter UI → dispatches START_QUIZ
    Quiz.jsx                   — question-by-question UI
    Results.jsx                — score, Supabase insert, PDF download, email
  components/
    QuestionCard.jsx            — *** UNCOMMITTED CHANGE (match-column reformat) ***
    ReviewCard.jsx              — *** UNCOMMITTED CHANGE (match-column reformat) ***
    OptionButton.jsx
    ProgressBar.jsx
    QuestionGrid.jsx
    Timer.jsx
  lib/
    supabase.js                — createClient wrapper
    generateReport.js          — buildReportPDF + buildReportText
  data/
    questions.js               — loadQuestions() (runtime fetch) + computeMetadata()
```

### Infrastructure
- **Vercel** deployment, SPA rewrites via `vercel.json`
- **Supabase** — `attempts` table (id, date, score, total, mode, duration_seconds, questions jsonb)
- **EmailJS** — sends plain-text report to user's email
- Secrets in `.env.local` (gitignored); must also be set in Vercel environment variables for production

### Git state
Latest commit: `c16278d Fix Config blank screen after async questions load`

**Two files have uncommitted changes** (the match-the-column fix from this session):
- `src/components/QuestionCard.jsx`
- `src/components/ReviewCard.jsx`

---

## Actively Edited Files This Session

| File | What changed |
|------|-------------|
| `src/components/QuestionCard.jsx` | Added `reformatMatchColumn()` — detects P./Q./R./S. or (P)/(Q)/(R)/(S) label patterns (≥3 hits), inserts `\n` before each label; also handles Column I/II headers. Applied to question text in the text-only rendering branch. |
| `src/components/ReviewCard.jsx` | Same `reformatMatchColumn()` added and applied to both the collapsed preview line and the expanded full text. |

---

## Things That Failed / Dead Ends

### Async refactor (now fixed, but worth knowing)
When `questions.js` was changed from a static import to `loadQuestions()` (runtime fetch), three bugs appeared together:
1. `applyFilters` in Config.jsx referenced a module-level `questions` variable that no longer existed → ReferenceError before the loading guard could run. Fix: pass `questions` as a parameter.
2. `availableTopics` useMemo was missing `questions` in its deps array → stale closure after fetch resolved. Fix: added to deps.
3. `PRESETS` useMemo used the `ALL_YEARS` array ref (which is `metadata?.years ?? []`) as a dep → new array reference every render → infinite re-render. Fix: dep on `metadata` object instead.
The "blank Config screen" bug was a symptom of all three hitting at once.

### GitHub Pages → abandoned
Originally deployed to GitHub Pages with `base: '/neetquiz/'` in `vite.config.js` and a 404.html redirect hack for SPA routing. Abandoned in favor of Vercel because Pages couldn't serve the SPA routes cleanly. All `BASE_URL` usage in the code is still correct for Vercel (BASE_URL is `/`).

### `metadata.years.map(Number)` → broke mock years
Mock test questions use string years like `"MOCK-1"`. An early version of `computeMetadata` called `.map(Number)` on year keys, turning `"MOCK-1"` into `NaN`. The filter then silently excluded all mock questions. Fixed by preserving original types (numbers stay numbers, strings stay strings).

### Questions.json in the bundle
Originally imported as `import raw from '../../public/questions.json'` — this caused a 2.6 MB JS chunk that blew past Vite's bundle size warning. Switched to runtime `fetch()` in `loadQuestions()`. The tradeoff is a loading spinner on first visit, which is acceptable.

### EmailJS "public key required" on deployed build
Local builds worked because `.env.local` had the keys. The deployed Vercel build did not — the `VITE_EMAILJS_*` environment variables had not been added in the Vercel dashboard. The fix is to add them there; `.env.local` is enough for local dev.

### Match-the-column regex: lookbehind attempt
Tried a variable-length negative lookbehind (`(?<!Match\s{0,10})`) to avoid splitting "Match Column-I" intro sentences. JS lookbehinds only support fixed-length patterns — this throws at runtime. Reverted to the simpler regex; the slight "Match\nColumn-I" split in intro text is acceptable.

---

## Bug Investigation Results

### Bug 1 — question/option mismatch (reported by user)
**Conclusion: no data corruption found in current questions.json.**
- `2016_q33` is correctly labeled Physics with matching Physics options.
- `2017_q133` has "sticky character" biology text but is correctly labeled Biology.
- Zero questions have a subject mismatch between their `subject` field and q_number range.
- Zero cross-year text contamination.
- One embedded number artifact: `mock2_q1` text starts with "6." (PDF extraction artifact), but options are correct.
- 19 "cross-subject text suspects" reviewed — all are legitimate interdisciplinary questions.

The reported bug was almost certainly seen on a pre-fix build (before the blank Config screen fix or before mock years were corrected).

### Bug 2 — match-the-column unreadable (fixed this session)
5 questions confirmed with match-the-column format: `2021_q8`, `2021_q18`, `2017_q9`, `mock2_q81`, `mock2_q89`. The `reformatMatchColumn` function now makes all 5 readable. No JSON changes — display layer only.

---

## Next Steps (in priority order)

1. **Commit the match-column fix** — `QuestionCard.jsx` and `ReviewCard.jsx` are currently uncommitted. Commit message: `Fix: reformat match-the-column questions for readability`.

2. **Add Vercel env vars for EmailJS** — Go to Vercel dashboard → project settings → Environment Variables. Add `VITE_EMAILJS_SERVICE_ID`, `VITE_EMAILJS_TEMPLATE_ID`, `VITE_EMAILJS_PUBLIC_KEY`. Without these, the "Email report" button on the Results page will fail in production.

3. **Delete orphaned probe images** — ~15 files in `public/images/` like `del_mid5x.png`, `probe_page7.png` are debug artifacts from PDF extraction. Safe to delete; they're not referenced by any question.

4. **Math rendering** — Physics and Chemistry questions with equations currently show a warning ("mathematical symbols may not display correctly"). `src/utils/renderMath.js` has a `hasMath()` detector but it's not wired to anything. The logical next step is to add KaTeX rendering: install `katex`, detect LaTeX-like strings, render inline. The tricky part is that the equations in questions.json are plain text (e.g. `ρ 2 m ne`), not LaTeX — so proper math rendering would require either re-extracting with LaTeX output or writing a normalizer.

5. **Difficulty data** — The `difficulty` filter in Config is wired up but has no effect because no questions have a `difficulty` field (the hint text says so). If you want to add difficulty, it would have to be either scraped from a source or ML-tagged.
