import type { components } from '@/api/schema'

import { prescriptionFields } from './prescription'
import { createSessionPdf, INK, MUTED, type SessionPdf } from './sessionPdf'
import { evaluateTargetTime, formatTargetTime } from './targetTime'
import { categoryLabels, subtypeLabels } from './trainingLabels'

type TrainingDetail = components['schemas']['TrainingSessionDetailResponse']
type ItemResponse = components['schemas']['ItemResponse']

/** A pool item's target time for the PDF: the computed seconds when the athlete's
 *  personal best is known, otherwise the bare formula (matching the on-screen fallback). */
function targetTimeLabel(item: ItemResponse, personalBest: number | null): string {
  if (item.target_time_formula == null) return ''
  const seconds =
    personalBest != null ? evaluateTargetTime(item.target_time_formula, personalBest) : null
  const value = seconds != null ? formatTargetTime(seconds) : item.target_time_formula
  return `Tiempo objetivo: ${value}`
}

/** The prescription line for a series item, e.g. "Series: 4 · Reps/serie: 8". */
function itemLine(item: ItemResponse, personalBest: number | null): string {
  const name = item.exercise_name ?? 'Ejercicio'
  const fields = prescriptionFields(item)
  const suffix = fields.map((f) => `${f.label}: ${f.value}`).join(' · ')
  const load = item.load_percentage != null ? `Carga: ${item.load_percentage}%` : ''
  const target = targetTimeLabel(item, personalBest)
  const extras = [suffix, load, target].filter(Boolean).join(' · ')
  return extras ? `${name} — ${extras}` : name
}

/** Render one training into the given PDF (no page handling — the caller decides
 *  page breaks between sessions). `personalBest` (seconds, or null) turns pool items'
 *  target-time formulas into computed times. */
function renderTraining(
  pdf: SessionPdf,
  training: TrainingDetail,
  personalBest: number | null,
): void {
  // Header: title + category/subtype, flowing inside the first column.
  pdf.write(training.title ?? 'Sin título', { size: 16, style: 'bold', lineH: 7 })
  pdf.write(`${categoryLabels[training.category]} · ${subtypeLabels[training.subtype]}`, {
    size: 9,
    color: MUTED,
    lineH: 5,
  })
  pdf.space(1)
  pdf.rule()
  pdf.space(4)

  if (training.blocks.length === 0) {
    pdf.write('Este entrenamiento no tiene bloques.', { size: 10, color: MUTED, lineH: 6 })
  }

  for (const block of training.blocks) {
    pdf.ensure(8)
    pdf.write(block.name, { size: 12, style: 'bold', lineH: 6 })

    for (const sub of block.sub_blocks) {
      pdf.ensure(6)
      pdf.write(sub.name, { indent: 4, size: 10, style: 'bold', lineH: 5.5 })
      if (sub.notes) {
        pdf.write(sub.notes, { indent: 4, size: 8.5, color: MUTED, lineH: 4.5 })
      }

      sub.items.forEach((item, index) => {
        const text =
          item.kind === 'note' ? (item.text ?? '') : `${index + 1}. ${itemLine(item, personalBest)}`
        if (!text) return
        const color = item.kind === 'note' ? MUTED : INK
        pdf.write(text, { indent: 8, size: 9, color, lineH: 5 })
        // Series items can carry an extra note below the prescription (notes use their
        // text as the line itself, so only add this for series). Matches the on-screen
        // view, which shows this commentary under the exercise.
        if (item.kind === 'series' && item.text) {
          pdf.write(item.text, { indent: 11, size: 8.5, color: MUTED, lineH: 4.5 })
        }
      })

      pdf.space(1.5)
    }
    pdf.space(2)
  }
}

/** Generate a print-ready landscape-A5 PDF of a gym/pool training session and open
 *  it in a new tab. Vector text, two columns per page (see sessionPdf). `personalBest`
 *  (seconds, or null) computes pool items' target times; null prints the formula. */
export function openTrainingPdf(
  training: TrainingDetail,
  personalBest: number | null = null,
): void {
  const pdf = createSessionPdf()
  renderTraining(pdf, training, personalBest)
  pdf.open(`${training.title ?? 'entrenamiento'}.pdf`)
}

/** Generate one PDF holding several trainings, each starting on a new page. */
export function openTrainingsPdf(
  trainings: TrainingDetail[],
  personalBest: number | null = null,
): void {
  const pdf = createSessionPdf()
  trainings.forEach((training, index) => {
    if (index > 0) pdf.pageBreak()
    renderTraining(pdf, training, personalBest)
  })
  pdf.open('entrenamientos.pdf')
}
