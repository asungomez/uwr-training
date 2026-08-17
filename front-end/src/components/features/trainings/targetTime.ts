/** Target-time formulas for pool exercises: a tiny, safe evaluator for arithmetic over
 *  `pb` (the athlete's latest lactic personal best, in seconds). Mirrors the backend
 *  grammar (numbers, `pb`, `+ - * /`, unary ±, parentheses). Uses a hand-written parser —
 *  never `eval`/`Function` — and returns null for anything malformed (the backend
 *  validates formulas on save, so a null here is a defensive fallback, not the norm). */

type Token = string

function tokenize(input: string): Token[] | null {
  const tokens: Token[] = []
  // Sticky match: optional leading whitespace, then one token (a number, `pb`, or a
  // single operator/paren). Anything else → unmatched → invalid.
  const re = /\s*([0-9]*\.?[0-9]+|pb|[+\-*/()])/y
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

export function evaluateTargetTime(formula: string, pb: number): number | null {
  const maybeTokens = tokenize(formula)
  if (!maybeTokens) return null
  const tokens: Token[] = maybeTokens // pin non-null so the nested parsers narrow it
  let pos = 0
  const peek = (): Token | undefined => tokens[pos]

  // Recursive descent with standard precedence: expr (+ -) → term (* /) → factor (unary)
  // → primary (number | pb | parenthesised expr).
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
      const value = factor()
      if (value === null) return null
      return op === '-' ? -value : value
    }
    return primary()
  }
  function primary(): number | null {
    const token = peek()
    if (token === undefined) return null
    if (token === '(') {
      pos++
      const value = expr()
      if (value === null || tokens[pos++] !== ')') return null
      return value
    }
    if (token === 'pb') {
      pos++
      return pb
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

/** Format a time in seconds the way the lactic-test tables do: one decimal, trailing
 *  zero trimmed (28.0 → "28"), with the unit. */
export function formatTargetTime(seconds: number): string {
  return `${Number(seconds.toFixed(1))} s`
}
