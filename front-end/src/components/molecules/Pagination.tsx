import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  page: number
  pageCount: number
  onPageChange: (page: number) => void
}

/** Page numbers to show, with `'ellipsis'` gaps: e.g. 1 … 4 5 6 … 10. */
function pageWindow(page: number, pageCount: number): (number | 'ellipsis')[] {
  const pages = new Set<number>([1, pageCount, page, page - 1, page + 1])
  const visible = [...pages].filter((p) => p >= 1 && p <= pageCount).sort((a, b) => a - b)

  const result: (number | 'ellipsis')[] = []
  let previous = 0
  for (const p of visible) {
    if (p - previous > 1) result.push('ellipsis')
    result.push(p)
    previous = p
  }
  return result
}

function Pagination({ page, pageCount, onPageChange }: PaginationProps) {
  if (pageCount <= 1) return null

  const arrowClass =
    'inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-300 transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40'

  return (
    <nav className="mt-6 flex items-center justify-center gap-1" aria-label="Paginación">
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        aria-label="Página anterior"
        className={arrowClass}
      >
        <ChevronLeft size={16} />
      </button>

      {pageWindow(page, pageCount).map((item, index) =>
        item === 'ellipsis' ? (
          <span key={`ellipsis-${index}`} className="px-2 text-slate-500">
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            onClick={() => onPageChange(item)}
            aria-current={item === page ? 'page' : undefined}
            className={`inline-flex h-8 min-w-8 items-center justify-center rounded-md px-2 text-sm font-medium transition-colors ${
              item === page ? 'bg-indigo-600 text-white' : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            {item}
          </button>
        ),
      )}

      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= pageCount}
        aria-label="Página siguiente"
        className={arrowClass}
      >
        <ChevronRight size={16} />
      </button>
    </nav>
  )
}

export default Pagination
