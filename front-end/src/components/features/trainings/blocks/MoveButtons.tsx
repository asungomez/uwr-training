import { ChevronDown, ChevronUp } from 'lucide-react'

interface MoveButtonsProps {
  /** Hidden on the first item of its list (nothing above to swap with). */
  canMoveUp: boolean
  /** Hidden on the last item of its list (nothing below to swap with). */
  canMoveDown: boolean
  onMoveUp: () => void
  onMoveDown: () => void
  label: string
  /** Extra classes for the wrapper (e.g. top margin to align with a drag handle). */
  className?: string
}

/** Up/down chevrons to reorder an item one position — a touch-friendly
 *  alternative to dragging on mobile. Both chevrons are always shown; the unusable
 *  edge one (no up on the first, no down on the last) is disabled rather than hidden,
 *  so the control's footprint is stable and the move-down chevron is visually
 *  distinct from a collapse toggle. */
function MoveButtons({
  canMoveUp,
  canMoveDown,
  onMoveUp,
  onMoveDown,
  label,
  className = '',
}: MoveButtonsProps) {
  const btn =
    'rounded p-1 text-slate-500 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none disabled:cursor-not-allowed disabled:text-slate-700 disabled:hover:bg-transparent disabled:hover:text-slate-700'
  return (
    <div className={`flex flex-col ${className}`}>
      <button
        type="button"
        onClick={onMoveUp}
        disabled={!canMoveUp}
        aria-label={`Subir ${label}`}
        className={btn}
      >
        <ChevronUp size={14} />
      </button>
      <button
        type="button"
        onClick={onMoveDown}
        disabled={!canMoveDown}
        aria-label={`Bajar ${label}`}
        className={btn}
      >
        <ChevronDown size={14} />
      </button>
    </div>
  )
}

export default MoveButtons
