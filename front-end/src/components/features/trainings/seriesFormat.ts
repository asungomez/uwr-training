/** Helpers for the series prescription fields: time is stored as whole seconds
 *  but entered/displayed as mm:ss; distance is stored as whole meters. */

/** Parse a mm:ss (or plain seconds) string to whole seconds. Returns null for
 *  blank/invalid input so the field stays optional. */
export function parseTimeToSeconds(value: string): number | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  const parts = trimmed.split(':')
  if (parts.length === 1) {
    const seconds = Number(parts[0])
    return Number.isInteger(seconds) && seconds >= 0 ? seconds : null
  }
  if (parts.length === 2) {
    const minutes = Number(parts[0])
    const seconds = Number(parts[1])
    if (
      Number.isInteger(minutes) &&
      Number.isInteger(seconds) &&
      minutes >= 0 &&
      seconds >= 0 &&
      seconds < 60
    ) {
      return minutes * 60 + seconds
    }
  }
  return null
}

/** Format whole seconds as mm:ss (e.g. 90 → "1:30"). Empty string for null. */
export function formatSecondsAsTime(seconds: number | null | undefined): string {
  if (seconds == null) return ''
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  return `${minutes}:${String(rest).padStart(2, '0')}`
}

/** Parse a whole-number string to a non-negative integer, or null if blank/invalid. */
export function parseOptionalInt(value: string): number | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  const parsed = Number(trimmed)
  return Number.isInteger(parsed) && parsed >= 0 ? parsed : null
}

/** Parse a possibly-fractional number string (e.g. "55.6") to a non-negative
 *  number, or null if blank/invalid. Accepts comma decimals. */
export function parseOptionalNumber(value: string): number | null {
  const trimmed = value.trim().replace(',', '.')
  if (!trimmed) return null
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null
}
