/** Target-time formulas for pool exercises: a tiny, safe evaluator for arithmetic over
 *  one test variable — `pb` (latest lactic personal best) or `st` (latest speed-test
 *  result), both in seconds. A formula references exactly one of them. Mirrors the
 *  backend grammar (numbers, the variable, `+ - * /`, unary ±, parentheses). Uses a
 *  hand-written parser — never `eval`/`Function`. The backend validates formulas on
 *  save, so a null result here is a defensive fallback, not the norm. */

export type TargetTimeVariable = 'pb' | 'st'

type Token = string

function tokenize(input: string): Token[] | null {
  const tokens: Token[] = []
  // Sticky match: optional leading whitespace, then one token (a number, `pb`/`st`, or a
  // single operator/paren). Anything else → unmatched → invalid.
  const re = /\s*([0-9]*\.?[0-9]+|pb|st|[+\-*/()])/y
  let i = 0
  while (i < input.length) {
    if (/^\s+$/.test(input.slice(i))) break // only trailing whitespace left
    re.lastIndex = i
    const match = re.exec(input)
    if (match?.[1] === undefined) return null
    tokens.push(match[1])
    i = re.lastIndex
  }
  return tokens
}

/** The single test variable a formula references, or null if it references none or both.
 *  Assumes a backend-validated formula; it doesn't re-check the arithmetic. */
export function formulaVariable(formula: string): TargetTimeVariable | null {
  const tokens = tokenize(formula)
  if (!tokens) return null
  const hasPb = tokens.includes('pb')
  const hasSt = tokens.includes('st')
  if (hasPb && !hasSt) return 'pb'
  if (hasSt && !hasPb) return 'st'
  return null
}

/** Evaluate a formula with its variable bound to `value`. Both `pb` and `st` tokens
 *  resolve to `value` — a valid formula only uses one, so this is unambiguous. */
export function evaluateTargetTime(formula: string, value: number): number | null {
  const maybeTokens = tokenize(formula)
  if (!maybeTokens) return null
  const tokens: Token[] = maybeTokens // pin non-null so the nested parsers narrow it
  let pos = 0
  const peek = (): Token | undefined => tokens[pos]

  // Recursive descent with standard precedence: expr (+ -) → term (* /) → factor (unary)
  // → primary (number | variable | parenthesised expr).
  function expr(): number | null {
    let left = term()
    if (left === null) return null
    while (peek() === '+' || peek() === '-') {
      const op = tokens[pos++]
      const right = term()
      if (right === null) return null
      left = op === '+' ? left + right : left - right
    }
    return left
  }
  function term(): number | null {
    let left = factor()
    if (left === null) return null
    while (peek() === '*' || peek() === '/') {
      const op = tokens[pos++]
      const right = factor()
      if (right === null) return null
      left = op === '*' ? left * right : left / right
    }
    return left
  }
  function factor(): number | null {
    if (peek() === '+' || peek() === '-') {
      const op = tokens[pos++]
      const operand = factor()
      if (operand === null) return null
      return op === '-' ? -operand : operand
    }
    return primary()
  }
  function primary(): number | null {
    const token = peek()
    if (token === undefined) return null
    if (token === '(') {
      pos++
      const value2 = expr()
      if (value2 === null || tokens[pos++] !== ')') return null
      return value2
    }
    if (token === 'pb' || token === 'st') {
      pos++
      return value
    }
    if (/^(?:[0-9]*\.)?[0-9]+$/.test(token)) {
      pos++
      return Number(token)
    }
    return null
  }

  const result = expr()
  if (result === null || pos !== tokens.length) return null // leftover tokens → invalid
  return Number.isFinite(result) ? result : null
}

/** Resolve a formula against the athlete's latest test values: which variable it uses,
 *  that source value, and the computed target seconds (null when the source is missing
 *  or the formula is malformed). */
export function resolveTargetTime(
  formula: string,
  pb: number | null,
  st: number | null,
): { variable: TargetTimeVariable | null; sourceValue: number | null; seconds: number | null } {
  const variable = formulaVariable(formula)
  const sourceValue = variable === 'pb' ? pb : variable === 'st' ? st : null
  const seconds =
    variable !== null && sourceValue !== null ? evaluateTargetTime(formula, sourceValue) : null
  return { variable, sourceValue, seconds }
}

/** Per-variable copy for the computed tooltip (cites the source value) and the
 *  no-result warning. */
export const targetTimeMessages: Record<
  TargetTimeVariable,
  { computed: (sourceSeconds: number) => string; warning: string }
> = {
  pb: {
    computed: (s) => `Calculado a partir de tu última marca personal (${formatTargetTime(s)})`,
    warning: 'Haz una prueba de ácido láctico para calcular el tiempo objetivo',
  },
  st: {
    computed: (s) =>
      `Calculado a partir de tu último resultado de velocidad (${formatTargetTime(s)})`,
    warning: 'Haz una prueba de velocidad para calcular el tiempo objetivo',
  },
}

/** Format a time in seconds the way the lactic-test tables do: one decimal, trailing
 *  zero trimmed (28.0 → "28"), with the unit. */
export function formatTargetTime(seconds: number): string {
  return `${Number(seconds.toFixed(1))} s`
}
