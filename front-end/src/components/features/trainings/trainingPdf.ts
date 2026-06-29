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

// Two text columns per page: lines are short, so this fits far more before a
// page break (helps keep a whole training on one sheet).
const COL_GAP = 8
const COL_W = (PAGE_W - MARGIN * 2 - COL_GAP) / 2
const BOTTOM = PAGE_H - MARGIN

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
 *  new tab. Pure client-side (jsPDF), vector text — crisp and selectable. Content
 *  flows in two columns per page (left, then right, then a new page) to fit more
 *  and keep most trainings on a single sheet. */
export function openTrainingPdf(training: TrainingDetail): void {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a5' })

  // The current column's left edge and the running vertical cursor. Columns always
  // start at the top margin — the header is part of the first column's flow, not a
  // full-width band, so the right column reaches the top of the page too.
  let colX = MARGIN
  let y = MARGIN

  /** Move to the next column, or a new page after the second column. */
  function nextColumn(): void {
    if (colX === MARGIN) {
      colX = MARGIN + COL_W + COL_GAP
    } else {
      doc.addPage()
      colX = MARGIN
    }
    y = MARGIN
  }

  /** Ensure `needed` mm fit before the bottom margin, else flow to the next column. */
  function ensure(needed: number): void {
    if (y + needed > BOTTOM) nextColumn()
  }

  /** Write wrapped text in the current column. `indent` offsets within the column
   *  (and narrows the wrap width to match); advances y. */
  function writeWrapped(
    text: string,
    opts: {
      indent?: number
      size: number
      style?: 'normal' | 'bold'
      color?: number
      lineH: number
    },
  ): void {
    const { indent = 0, size, style = 'normal', color = INK, lineH } = opts
    doc.setFont('helvetica', style)
    doc.setFontSize(size)
    doc.setTextColor(color)
    const lines = doc.splitTextToSize(text, COL_W - indent) as string[]
    for (const line of lines) {
      ensure(lineH)
      doc.text(line, colX + indent, y)
      y += lineH
    }
  }

  // Header: title + category/subtype, flowing inside the first column (not a
  // full-width band) so both columns start at the top of the page.
  writeWrapped(training.title ?? 'Sin título', { size: 16, style: 'bold', lineH: 7 })
  writeWrapped(`${categoryLabels[training.category]} · ${subtypeLabels[training.subtype]}`, {
    size: 9,
    color: MUTED,
    lineH: 5,
  })
  y += 1
  doc.setDrawColor(200)
  doc.line(colX, y, colX + COL_W, y)
  y += 4

  if (training.blocks.length === 0) {
    writeWrapped('Este entrenamiento no tiene bloques.', { size: 10, color: MUTED, lineH: 6 })
  }

  for (const block of training.blocks) {
    ensure(8)
    writeWrapped(block.name, { size: 12, style: 'bold', lineH: 6 })

    for (const sub of block.sub_blocks) {
      ensure(6)
      writeWrapped(sub.name, { indent: 4, size: 10, style: 'bold', lineH: 5.5 })
      if (sub.notes) {
        writeWrapped(sub.notes, { indent: 4, size: 8.5, color: MUTED, lineH: 4.5 })
      }

      sub.items.forEach((item, index) => {
        const text = item.kind === 'note' ? (item.text ?? '') : `${index + 1}. ${itemLine(item)}`
        if (!text) return
        const color = item.kind === 'note' ? MUTED : INK
        writeWrapped(text, { indent: 8, size: 9, color, lineH: 5 })
      })

      y += 1.5
    }
    y += 2
  }

  // Open in a new tab; the browser's PDF viewer offers print/save.
  doc.output('dataurlnewwindow', { filename: `${training.title ?? 'entrenamiento'}.pdf` })
}
