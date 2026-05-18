import jsPDF from 'jspdf'

const LABELS = ['A', 'B', 'C', 'D']

function fmt(ms) {
  const s = Math.floor(Math.max(0, ms) / 1000)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${sec}s`
  return `${sec}s`
}

export function buildReportPDF({ questions, answers, score, duration, mode, startTime }) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  const ML = 15, MR = 15, W = 210, CW = W - ML - MR
  let y = 20

  const bump = (n = 5) => { y += n }
  const rule = (color = [220, 220, 220]) => {
    doc.setDrawColor(...color); doc.line(ML, y, W - MR, y)
  }
  const checkPage = (need = 20) => {
    if (y + need > 280) { doc.addPage(); y = 20 }
  }

  const date = startTime
    ? new Date(startTime).toLocaleDateString('en-IN', { dateStyle: 'long' })
    : new Date().toLocaleDateString('en-IN', { dateStyle: 'long' })
  const pct = score.maxScore > 0 ? Math.round((score.total / score.maxScore) * 100) : 0

  // ── Title ───────────────────────────────────────────────────────────────
  doc.setFontSize(20).setFont('helvetica', 'bold').setTextColor(20, 20, 20)
  doc.text('NEET Quiz Report', ML, y)
  bump(8)

  doc.setFontSize(8).setFont('helvetica', 'normal').setTextColor(120, 120, 120)
  doc.text(`${date}  ·  ${mode} mode  ·  ${fmt(duration)}  ·  ${questions.length} questions`, ML, y)
  bump(5)
  rule(); bump(6)

  // ── Score ────────────────────────────────────────────────────────────────
  doc.setFontSize(30).setFont('helvetica', 'bold').setTextColor(20, 20, 20)
  doc.text(`${score.total}`, ML, y)
  doc.setFontSize(16).setFont('helvetica', 'normal').setTextColor(140, 140, 140)
  doc.text(` / ${score.maxScore}`, ML + doc.getTextWidth(`${score.total}`), y)

  const pctRgb = pct >= 60 ? [22, 163, 74] : pct >= 40 ? [202, 138, 4] : [220, 38, 38]
  doc.setFontSize(22).setFont('helvetica', 'bold').setTextColor(...pctRgb)
  doc.text(`${pct}%`, ML + 55, y)
  bump(12)

  // Counts
  const chips = [
    { label: 'Correct',  n: score.correct,    rgb: [22, 163, 74]  },
    { label: 'Wrong',    n: score.wrong,       rgb: [220, 38, 38]  },
    { label: 'Skipped',  n: score.unanswered,  rgb: [100, 100, 100] },
  ]
  if (score.canceled > 0)
    chips.push({ label: 'Canceled', n: score.canceled, rgb: [161, 98, 7] })

  chips.forEach(({ label, n, rgb }, i) => {
    const x = ML + i * 42
    doc.setFontSize(16).setFont('helvetica', 'bold').setTextColor(...rgb)
    doc.text(String(n), x, y)
    doc.setFontSize(7).setFont('helvetica', 'normal').setTextColor(130, 130, 130)
    doc.text(label, x, y + 4)
  })
  bump(12)
  rule(); bump(6)

  // ── Subject breakdown ────────────────────────────────────────────────────
  doc.setFontSize(11).setFont('helvetica', 'bold').setTextColor(50, 50, 50)
  doc.text('Subject Breakdown', ML, y); bump(6)

  const cx = { s: ML, ok: ML + 68, bad: ML + 90, skip: ML + 112, sc: W - MR }
  doc.setFontSize(7).setFont('helvetica', 'bold').setTextColor(150, 150, 150)
  doc.text('SUBJECT', cx.s, y)
  doc.text('CORRECT', cx.ok, y)
  doc.text('WRONG', cx.bad, y)
  doc.text('SKIPPED', cx.skip, y)
  doc.text('SCORE', cx.sc, y, { align: 'right' })
  bump(3); rule(); bump(4)

  for (const [subj, s] of Object.entries(score.bySubject)) {
    if (s.correct + s.wrong + s.unanswered + (s.canceled || 0) === 0) continue
    doc.setFontSize(9).setFont('helvetica', 'normal').setTextColor(40, 40, 40)
    doc.text(subj, cx.s, y)
    doc.setTextColor(22, 163, 74);  doc.text(String(s.correct),   cx.ok + 6,   y, { align: 'center' })
    doc.setTextColor(220, 38, 38);  doc.text(String(s.wrong),     cx.bad + 4,  y, { align: 'center' })
    doc.setTextColor(100, 100, 100);doc.text(String(s.unanswered),cx.skip + 5, y, { align: 'center' })
    doc.setFont('helvetica', 'bold').setTextColor(40, 40, 40)
    doc.text(`${s.total} / ${s.maxScore}`, cx.sc, y, { align: 'right' })
    doc.setFont('helvetica', 'normal')
    bump(6)
  }
  bump(2); rule(); bump(6)

  // ── Wrong answers ────────────────────────────────────────────────────────
  const wrong = questions.filter(q =>
    q.correct_answer !== null &&
    answers[q.id] != null &&
    answers[q.id] !== q.correct_answer
  )

  if (wrong.length === 0) {
    doc.setFontSize(10).setFont('helvetica', 'italic').setTextColor(100, 100, 100)
    doc.text('No wrong answers.', ML, y)
  } else {
    doc.setFontSize(11).setFont('helvetica', 'bold').setTextColor(50, 50, 50)
    doc.text(`Wrong Answers  (${wrong.length})`, ML, y); bump(6)

    wrong.forEach((q, i) => {
      checkPage(22)
      const yourLabel = LABELS[answers[q.id] - 1]
      const corrLabel = LABELS[q.correct_answer - 1]
      const yourText  = `${yourLabel}. ${q.options[answers[q.id] - 1] ?? ''}`.slice(0, 70)
      const corrText  = `${corrLabel}. ${q.options[q.correct_answer - 1] ?? ''}`.slice(0, 70)
      const raw = q.has_image ? `[Image] ${q.text}` : q.text
      const wrapped = doc.setFontSize(8).splitTextToSize(raw, CW - 8).slice(0, 2)

      doc.setFontSize(8).setFont('helvetica', 'bold').setTextColor(60, 60, 60)
      doc.text(`${i + 1}.`, ML, y)
      doc.setFont('helvetica', 'normal').setTextColor(40, 40, 40)
      doc.text(wrapped, ML + 6, y); bump(wrapped.length * 4)

      doc.setTextColor(220, 38, 38); doc.text(`Your answer:  ${yourText}`, ML + 6, y); bump(4)
      doc.setTextColor(22, 163, 74); doc.text(`Correct:      ${corrText}`, ML + 6, y); bump(4)
      doc.setFontSize(7).setTextColor(160, 160, 160)
      doc.text(`${q.year} Q${q.q_number} · ${q.subject}`, ML + 6, y); bump(6)
    })
  }

  // Footer
  const pages = doc.getNumberOfPages()
  for (let p = 1; p <= pages; p++) {
    doc.setPage(p)
    doc.setFontSize(7).setFont('helvetica', 'normal').setTextColor(180, 180, 180)
    doc.text(`NEET Quiz  ·  Page ${p} of ${pages}`, W / 2, 290, { align: 'center' })
  }

  return doc
}

// Plain-text version of the report for the EmailJS template body
export function buildReportText({ questions, answers, score, duration, mode, startTime }) {
  const date = startTime
    ? new Date(startTime).toLocaleDateString('en-IN', { dateStyle: 'long' })
    : new Date().toLocaleDateString('en-IN', { dateStyle: 'long' })
  const pct = score.maxScore > 0 ? Math.round((score.total / score.maxScore) * 100) : 0

  const lines = [
    `NEET Quiz Report — ${date}`,
    `Mode: ${mode}  |  Duration: ${fmt(duration)}  |  Questions: ${questions.length}`,
    '',
    `Score:  ${score.total} / ${score.maxScore}  (${pct}%)`,
    `Correct: ${score.correct}  |  Wrong: ${score.wrong}  |  Skipped: ${score.unanswered}`,
    '',
    'Subject Breakdown',
    '-'.repeat(50),
  ]

  for (const [subj, s] of Object.entries(score.bySubject)) {
    if (s.correct + s.wrong + s.unanswered + (s.canceled || 0) === 0) continue
    lines.push(`${subj.padEnd(14)} ✓${s.correct}  ✗${s.wrong}  –${s.unanswered}  ${s.total}/${s.maxScore}`)
  }

  const wrong = questions.filter(q =>
    q.correct_answer !== null &&
    answers[q.id] != null &&
    answers[q.id] !== q.correct_answer
  )

  if (wrong.length > 0) {
    lines.push('', `Wrong Answers (${wrong.length})`, '-'.repeat(50))
    wrong.slice(0, 30).forEach((q, i) => {
      const your  = `${LABELS[answers[q.id] - 1]}. ${q.options[answers[q.id] - 1] ?? ''}`.slice(0, 80)
      const corr  = `${LABELS[q.correct_answer - 1]}. ${q.options[q.correct_answer - 1] ?? ''}`.slice(0, 80)
      const qtext = (q.has_image ? `[Image] ${q.text}` : q.text).slice(0, 120)
      lines.push(
        `\n${i + 1}. ${qtext}`,
        `   Your answer: ${your}`,
        `   Correct:     ${corr}`,
        `   ${q.year} Q${q.q_number} · ${q.subject}`,
      )
    })
    if (wrong.length > 30) lines.push(`\n... and ${wrong.length - 30} more.`)
  }

  return lines.join('\n')
}
