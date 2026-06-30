/** Text for the cardio timer, split into two intentionally separate families:
 *
 *  - **Labels** — what's shown on screen ("Bloque 1/2 completado", "1min · 80%").
 *  - **Speech** — what's read aloud ("Bloque uno de dos completado", "Ochenta por
 *    ciento, un minuto").
 *
 *  They don't map 1:1: the screen is terse and numeric, speech is spelled-out and
 *  fluent. Keeping them apart means a wording change on one never silently drags
 *  the other along.
 */

import { formatDuration } from './cardioFormat'

type IntervalKind = 'effort' | 'rest'

// ---------------------------------------------------------------- screen labels

export function clockLabel(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

export function intervalLabel(
  kind: IntervalKind,
  durationSeconds: number,
  intensityPct: number | null,
): string {
  const duration = formatDuration(durationSeconds)
  if (kind === 'rest') return `${duration} descanso`
  return intensityPct != null ? `${duration} · ${intensityPct}%` : duration
}

export function trailingRestLabel(durationSeconds: number): string {
  return `Después: ${formatDuration(durationSeconds)} de descanso`
}

export function blockHeaderLabel(blockNumber: number, totalBlocks: number): string {
  return `Bloque ${blockNumber}/${totalBlocks}`
}

export function repetitionLabel(repeat: number, totalRepeats: number): string {
  return `Repetición ${repeat}/${totalRepeats}`
}

export function blockDoneLabel(blockNumber: number, totalBlocks: number): string {
  return `Bloque ${blockNumber}/${totalBlocks} completado`
}

export const FINISHED_LABEL = 'Entrenamiento finalizado'

// ---------------------------------------------------------------------- speech
//
// Spelled-out, fluent Spanish for the speech-synthesis voice. Engines verbalise
// bare digits inconsistently ("1 minuto" → "uno minuto"), so we spell numbers
// ourselves and apply the masculine apocope (un/veintiún) before minuto/segundo.

// 0–29 are irregular enough to just list; 30+ compose as "treinta y cinco".
const ONES = [
  'cero',
  'uno',
  'dos',
  'tres',
  'cuatro',
  'cinco',
  'seis',
  'siete',
  'ocho',
  'nueve',
  'diez',
  'once',
  'doce',
  'trece',
  'catorce',
  'quince',
  'dieciséis',
  'diecisiete',
  'dieciocho',
  'diecinueve',
  'veinte',
  'veintiuno',
  'veintidós',
  'veintitrés',
  'veinticuatro',
  'veinticinco',
  'veintiséis',
  'veintisiete',
  'veintiocho',
  'veintinueve',
]
const TENS: Record<number, string> = {
  30: 'treinta',
  40: 'cuarenta',
  50: 'cincuenta',
  60: 'sesenta',
  70: 'setenta',
  80: 'ochenta',
  90: 'noventa',
}

/** Cardinal number in words for 0–100 (the only range the timer needs:
 *  percentages, minutes, seconds). Out-of-range falls back to digits. */
function cardinal(n: number): string {
  if (n < 0) return String(n)
  if (n < 30) return ONES[n] ?? String(n)
  if (n === 100) return 'cien'
  if (n < 100) {
    const tens = TENS[Math.floor(n / 10) * 10]
    const unit = n % 10
    if (!tens) return String(n)
    return unit === 0 ? tens : `${tens} y ${ONES[unit]}`
  }
  return String(n)
}

/** Drop the final "o" of uno/veintiuno/…y uno before a masculine noun:
 *  "un minuto", "veintiún segundos", "treinta y un minutos". */
function apocope(words: string): string {
  if (words === 'uno') return 'un'
  if (words === 'veintiuno') return 'veintiún'
  if (words.endsWith(' y uno')) return `${words.slice(0, -3)}un`
  return words
}

function cap(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1)
}

function spokenDuration(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  const parts: string[] = []
  if (m > 0) parts.push(`${apocope(cardinal(m))} ${m === 1 ? 'minuto' : 'minutos'}`)
  if (s > 0) parts.push(`${apocope(cardinal(s))} ${s === 1 ? 'segundo' : 'segundos'}`)
  return parts.length > 0 ? parts.join(' y ') : 'cero segundos'
}

/** "Sesenta por ciento, un minuto" / "Descanso, tres minutos". */
export function speakInterval(
  kind: IntervalKind,
  durationSeconds: number,
  intensityPct: number | null,
): string {
  const duration = spokenDuration(durationSeconds)
  if (kind === 'rest') return cap(`descanso, ${duration}`)
  if (intensityPct == null) return cap(duration)
  return cap(`${cardinal(intensityPct)} por ciento, ${duration}`)
}

/** "Repetición tres de seis". */
export function speakRepetition(repeat: number, totalRepeats: number): string {
  return `Repetición ${cardinal(repeat)} de ${cardinal(totalRepeats)}`
}

/** "Bloque uno de dos completado". */
export function speakBlockDone(blockNumber: number, totalBlocks: number): string {
  return `Bloque ${cardinal(blockNumber)} de ${cardinal(totalBlocks)} completado`
}

export const SPEAK_FINISHED = 'Entrenamiento finalizado'
