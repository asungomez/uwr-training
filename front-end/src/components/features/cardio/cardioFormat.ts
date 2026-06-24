/** Format a duration in whole seconds for display: "45s", "1min", "1min 30s",
 *  "2min". Returns "" for null/zero so empty fields render nothing. */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null || seconds <= 0) return ''
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  if (minutes === 0) return `${rest}s`
  if (rest === 0) return `${minutes}min`
  return `${minutes}min ${rest}s`
}
