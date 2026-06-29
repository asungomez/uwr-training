import type { components } from '@/api/schema'

import {
  createSessionPdf,
  INK,
  MUTED,
  type SessionPdf,
} from '@/components/features/trainings/sessionPdf'

import { cardioSubtypeLabels } from './cardioLabels'
import { formatDuration } from './cardioFormat'

type CardioDetail = components['schemas']['CardioTrainingDetailResponse']
type IntervalResponse = components['schemas']['IntervalResponse']

/** One interval as a line, e.g. "1min 30s · 80%" or "30s descanso". */
function intervalLine(interval: IntervalResponse): string {
  const duration = formatDuration(interval.duration_seconds)
  if (interval.kind === 'rest') return `${duration} descanso`
  return interval.intensity_pct != null ? `${duration} · ${interval.intensity_pct}%` : duration
}

/** Render one cardio training into the given PDF (no page handling — the caller
 *  decides page breaks between sessions). */
function renderCardio(pdf: SessionPdf, training: CardioDetail): void {
  // Header: title + subtype, flowing inside the first column.
  pdf.write(training.title ?? 'Sin título', { size: 16, style: 'bold', lineH: 7 })
  pdf.write(`Cardio · ${cardioSubtypeLabels[training.subtype]}`, {
    size: 9,
    color: MUTED,
    lineH: 5,
  })
  pdf.space(1)
  pdf.rule()
  pdf.space(4)

  if (training.items.length === 0) {
    pdf.write('Este entrenamiento no tiene bloques.', { size: 10, color: MUTED, lineH: 6 })
  }

  for (const item of training.items) {
    if (item.kind === 'note') {
      if (item.text) pdf.write(item.text, { size: 9, color: MUTED, lineH: 5 })
      continue
    }

    pdf.ensure(8)
    pdf.write(item.repeats > 1 ? `Repetir ${item.repeats} veces` : 'Una vez', {
      size: 11,
      style: 'bold',
      lineH: 6,
    })

    item.intervals.forEach((interval, index) => {
      const color = interval.kind === 'rest' ? MUTED : INK
      pdf.write(`${index + 1}. ${intervalLine(interval)}`, { indent: 6, size: 9, color, lineH: 5 })
    })

    if (item.rest_seconds != null && item.rest_seconds > 0) {
      pdf.write(`Después: ${formatDuration(item.rest_seconds)} de descanso`, {
        indent: 6,
        size: 8.5,
        color: MUTED,
        lineH: 4.5,
      })
    }

    pdf.space(2)
  }
}

/** Generate a print-ready landscape-A5 PDF of a cardio training and open it in a
 *  new tab. Vector text, two columns per page (see sessionPdf). */
export function openCardioPdf(training: CardioDetail): void {
  const pdf = createSessionPdf()
  renderCardio(pdf, training)
  pdf.open(`${training.title ?? 'cardio'}.pdf`)
}

/** Generate one PDF holding several cardio trainings, each starting on a new page. */
export function openCardiosPdf(trainings: CardioDetail[]): void {
  const pdf = createSessionPdf()
  trainings.forEach((training, index) => {
    if (index > 0) pdf.pageBreak()
    renderCardio(pdf, training)
  })
  pdf.open('entrenamientos-cardio.pdf')
}
