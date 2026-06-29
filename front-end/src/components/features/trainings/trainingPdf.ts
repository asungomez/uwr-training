import type { components } from '@/api/schema'

import { prescriptionFields } from './prescription'
import { createSessionPdf, INK, MUTED } from './sessionPdf'
import { categoryLabels, subtypeLabels } from './trainingLabels'

type TrainingDetail = components['schemas']['TrainingSessionDetailResponse']
type ItemResponse = components['schemas']['ItemResponse']

/** The prescription line for a series item, e.g. "Series: 4 · Reps/serie: 8". */
function itemLine(item: ItemResponse): string {
  const name = item.exercise_name ?? 'Ejercicio'
  const fields = prescriptionFields(item)
  const suffix = fields.map((f) => `${f.label}: ${f.value}`).join(' · ')
  const load = item.load_percentage != null ? `Carga: ${item.load_percentage}%` : ''
  const extras = [suffix, load].filter(Boolean).join(' · ')
  return extras ? `${name} — ${extras}` : name
}

/** Generate a print-ready landscape-A5 PDF of a gym/pool training session and open
 *  it in a new tab. Vector text, two columns per page (see sessionPdf). */
export function openTrainingPdf(training: TrainingDetail): void {
  const pdf = createSessionPdf()

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
        const text = item.kind === 'note' ? (item.text ?? '') : `${index + 1}. ${itemLine(item)}`
        if (!text) return
        const color = item.kind === 'note' ? MUTED : INK
        pdf.write(text, { indent: 8, size: 9, color, lineH: 5 })
      })

      pdf.space(1.5)
    }
    pdf.space(2)
  }

  pdf.open(`${training.title ?? 'entrenamiento'}.pdf`)
}
