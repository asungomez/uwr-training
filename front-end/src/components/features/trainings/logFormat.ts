/** Format an ISO timestamp as a Spanish long date + time, for session logs. */
export function formatLogDate(value: string): string {
  return new Date(value).toLocaleString('es-ES', { dateStyle: 'long', timeStyle: 'short' })
}
