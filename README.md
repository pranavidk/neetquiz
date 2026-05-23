# NEET PYQ Quiz

React + Vite + Tailwind quiz app for 1880 NEET previous-year questions (2016–2025).

## Setup

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # production build → dist/
npm run preview   # preview the build locally
```

## Images

Question diagrams live in `public/images/` and are served at `/images/<filename>`.

**If the source `images/` folder at the project root is updated, re-copy manually:**

```bash
rm -rf public/images && cp -r images/ public/images/
```

The `public/images/` copy exists because symlinks break on Windows and GitHub Pages.

## Data

- `questions.json` — 1880 MCQs; imported at build time (bundled into JS)
- 8 questions have `correct_answer: null` (NTA-canceled; not counted in score)
- 119 questions have `is_deleted_topic: true` (hidden by default in Config)

## Scoring

NEET formula: **+4** correct · **−1** wrong · **0** unattempted/canceled

## Deployment

### Vercel

Use the Vite preset, with:

- Build command: `npm run build`
- Output directory: `dist`

Add these Environment Variables in Vercel for Production, Preview, and Development:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_EMAILJS_SERVICE_ID`
- `VITE_EMAILJS_TEMPLATE_ID`
- `VITE_EMAILJS_PUBLIC_KEY`

The app will still load if Supabase or EmailJS variables are missing, but those integrations will be skipped or show an error until the variables are set.

### GitHub Pages

```bash
npm run build
# push dist/ to gh-pages branch, or configure your CI
```
