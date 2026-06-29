import { jsPDF } from 'jspdf'

import type { components } from '@/api/schema'

import { prescriptionFields } from './prescription'
import { categoryLabels, subtypeLabels } from './trainingLabels'

type TrainingDetail = components['schemas']['TrainingSessionDetailResponse']
type ItemResponse = components['schemas']['ItemResponse']

// A5 landscape in mm — two fit on one A4 portrait sheet when printed 2-up.
const PAGE_W = 210
const PAGE_H = 148
const MARGIN = 12

// Greys (jsPDF works in 0–255 RGB).
const INK = 30
const MUTED = 110

/** The prescription line for a series item, e.g. "Series: 4 · Reps/serie: 8". */
function itemLine(item: ItemResponse): string {
  const name = item.exercise_name ?? 'Ejercicio'
  const fields = prescriptionFields(item)
  const suffix = fields.map((f) => `${f.label}: ${f.value}`).join(' · ')
  const load = item.load_percentage != null ? `Carga: ${item.load_percentage}%` : ''
  const extras = [suffix, load].filter(Boolean).join(' · ')
  return extras ? `${name} — ${extras}` : name
}

/** Generate a print-ready landscape-A5 PDF of a training session and open it in a
 *  new tab. Pure client-side (jsPDF), vector text — crisp and selectable. */
export function openTrainingPdf(training: TrainingDetail): void {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a5' })

  let y = MARGIN

  /** Start a fresh page and reset the cursor. */
  function newPage(): void {
    doc.addPage()
    y = MARGIN
  }

  /** Ensure `needed` mm fit before the bottom margin, else page-break. */
  function ensure(needed: number): void {
    if (y + needed > PAGE_H - MARGIN) newPage()
  }

  /** Write wrapped text at the given x/size/colour; advances y. Returns nothing. */
  function writeWrapped(
    text: string,
    opts: { x?: number; size: number; style?: 'normal' | 'bold'; color?: number; lineH: number },
  ): void {
    const { x = MARGIN, size, style = 'normal', color = INK, lineH } = opts
    doc.setFont('helvetica', style)
    doc.setFontSize(size)
    doc.setTextColor(color)
    const lines = doc.splitTextToSize(text, PAGE_W - MARGIN - x) as string[]
    for (const line of lines) {
      ensure(lineH)
      doc.text(line, x, y)
      y += lineH
    }
  }

  // Header: title + category/subtype.
  writeWrapped(training.title ?? 'Sin título', { size: 16, style: 'bold', lineH: 7 })
  writeWrapped(`${categoryLabels[training.category]} · ${subtypeLabels[training.subtype]}`, {
    size: 9,
    color: MUTED,
    lineH: 5,
  })
  y += 2
  doc.setDrawColor(200)
  doc.line(MARGIN, y, PAGE_W - MARGIN, y)
  y += 5

  if (training.blocks.length === 0) {
    writeWrapped('Este entrenamiento no tiene bloques.', { size: 10, color: MUTED, lineH: 6 })
  }

  for (const block of training.blocks) {
    ensure(8)
    writeWrapped(block.name, { size: 12, style: 'bold', lineH: 6 })

    for (const sub of block.sub_blocks) {
      ensure(6)
      writeWrapped(sub.name, { x: MARGIN + 4, size: 10, style: 'bold', lineH: 5.5 })
      if (sub.notes) {
        writeWrapped(sub.notes, { x: MARGIN + 4, size: 8.5, color: MUTED, lineH: 4.5 })
      }

      sub.items.forEach((item, index) => {
        const text = item.kind === 'note' ? (item.text ?? '') : `${index + 1}. ${itemLine(item)}`
        if (!text) return
        const color = item.kind === 'note' ? MUTED : INK
        writeWrapped(text, { x: MARGIN + 8, size: 9, color, lineH: 5 })
      })

      y += 1.5
    }
    y += 2
  }

  // Open in a new tab; the browser's PDF viewer offers print/save.
  doc.output('dataurlnewwindow', { filename: `${training.title ?? 'entrenamiento'}.pdf` })
}
