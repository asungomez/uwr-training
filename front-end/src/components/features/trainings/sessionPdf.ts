import { jsPDF } from 'jspdf'

// A5 landscape in mm — two fit on one A4 portrait sheet when printed 2-up.
const PAGE_W = 210
const PAGE_H = 148
const MARGIN = 12

// Two text columns per page: lines are short, so this fits far more before a
// page break (helps keep a whole session on one sheet).
const COL_GAP = 8
const COL_W = (PAGE_W - MARGIN * 2 - COL_GAP) / 2
const BOTTOM = PAGE_H - MARGIN

// Greys (jsPDF works in 0–255 RGB).
export const INK = 30
export const MUTED = 110

interface WriteOpts {
  indent?: number
  size: number
  style?: 'normal' | 'bold'
  color?: number
  lineH: number
}

/** A two-column, landscape-A5 PDF layout engine shared by the session sheets
 *  (gym/pool trainings and cardio). Content flows down the left column, then the
 *  right column, then a new page. */
export interface SessionPdf {
  /** Write wrapped text in the current column. `indent` offsets within the column
   *  (and narrows the wrap width to match); advances the cursor. */
  write(text: string, opts: WriteOpts): void
  /** Add vertical space (mm) within the current column. */
  space(mm: number): void
  /** A thin rule across the current column's width (e.g. under the header). */
  rule(): void
  /** Ensure `mm` fit before the bottom margin, else flow to the next column. */
  ensure(mm: number): void
  /** Start a fresh page in the left column (used between sessions in a multi-session
   *  export). No-op if nothing has been written yet. */
  pageBreak(): void
  /** Open the finished PDF in a new tab (the viewer offers print/save). */
  open(filename: string): void
}

export function createSessionPdf(): SessionPdf {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a5' })

  // Current column's left edge and the running vertical cursor. Columns always
  // start at the top margin — there's no full-width band, so both columns reach
  // the top of the page.
  let colX = MARGIN
  let y = MARGIN
  // Whether anything has been drawn yet (so pageBreak() doesn't add a blank lead page).
  let started = false

  function nextColumn(): void {
    if (colX === MARGIN) {
      colX = MARGIN + COL_W + COL_GAP
    } else {
      doc.addPage()
      colX = MARGIN
    }
    y = MARGIN
  }

  function ensure(mm: number): void {
    if (y + mm > BOTTOM) nextColumn()
  }

  function write(text: string, opts: WriteOpts): void {
    started = true
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

  function space(mm: number): void {
    y += mm
  }

  function rule(): void {
    doc.setDrawColor(200)
    doc.line(colX, y, colX + COL_W, y)
  }

  function pageBreak(): void {
    if (!started) return
    doc.addPage()
    colX = MARGIN
    y = MARGIN
  }

  function open(filename: string): void {
    doc.output('dataurlnewwindow', { filename })
  }

  return { write, space, rule, ensure, pageBreak, open }
}
