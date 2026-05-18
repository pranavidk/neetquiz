// Detects whether a string likely contains math content extracted as plain text.
// Used to decide rendering hints; full LaTeX rendering requires re-extraction as images.
const MATH_PATTERNS = [
  /\d\s+\d/,           // superscripts like "5 6" (meant to be 5⁶)
  /[α-ωΑ-Ω]/,         // Greek letters
  /lambda|alpha|beta|gamma|delta|theta|sigma|omega|pi\b/i,
  /\d+\/\d+/,          // fractions like 3/4
  /sqrt|sin|cos|tan|log|ln\b/i,
  /[²³⁰¹⁴⁵⁶⁷⁸⁹]/,   // unicode superscripts
  /[₀₁₂₃₄₅₆₇₈₉]/,   // unicode subscripts
]

export function hasMath(str) {
  if (!str) return false
  return MATH_PATTERNS.some(p => p.test(str))
}
