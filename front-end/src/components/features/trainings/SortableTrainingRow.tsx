import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { CalendarCheck, GripVertical, Hourglass } from 'lucide-react'

import type { components } from '@/api/schema'
import MoveButtons from '@/components/features/trainings/blocks/MoveButtons'

type TrainingSession = components['schemas']['TrainingSessionResponse']

const BLANK = 'Sin título'

function formatLastDone(value: string): string {
  return new Date(value).toLocaleDateString('es-ES', { dateStyle: 'long' })
}

interface SortableTrainingRowProps {
  session: TrainingSession
  /** Show the drag handle and move chevrons (admins only, and not while searching). */
  draggable: boolean
  onOpen: () => void
  /** Whether this row is ticked for the multi-session PDF export. */
  selected: boolean
  onToggleSelected: () => void
  /** False only on the very first training of the first page. */
  canMoveUp: boolean
  /** False only on the very last training of the last page. */
  canMoveDown: boolean
  /** Moves one position up, crossing to the previous page when at the top of this one. */
  onMoveUp: () => void
  /** Moves one position down, crossing to the next page when at the bottom of this one. */
  onMoveDown: () => void
}

function SortableTrainingRow({
  session,
  draggable,
  onOpen,
  selected,
  onToggleSelected,
  canMoveUp,
  canMoveDown,
  onMoveUp,
  onMoveDown,
}: SortableTrainingRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: session.id,
    disabled: !draggable,
  })

  const style = { transform: CSS.Transform.toString(transform), transition }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 transition-colors hover:bg-slate-700 ${isDragging ? 'z-10 opacity-60 shadow-xl' : ''}`}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggleSelected}
        aria-label={`Seleccionar ${session.title ?? BLANK}`}
        className="ml-3 size-4 shrink-0 accent-indigo-500"
      />
      {draggable && (
        /* Reorder controls: drag handle + move chevrons. Stacked vertically on
           mobile (scarce width), side-by-side from sm up. */
        <div className="ml-1 flex flex-col items-center sm:flex-row">
          <button
            type="button"
            {...attributes}
            {...listeners}
            aria-label="Reordenar entrenamiento"
            className="cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
          >
            <GripVertical size={18} />
          </button>

          <MoveButtons
            canMoveUp={canMoveUp}
            canMoveDown={canMoveDown}
            onMoveUp={onMoveUp}
            onMoveDown={onMoveDown}
            label="entrenamiento"
          />
        </div>
      )}
      <button
        type="button"
        onClick={onOpen}
        className="flex flex-1 flex-col gap-0.5 py-4 pr-4 pl-3 text-left focus:outline-none"
      >
        <span className="font-medium text-slate-100">
          {session.title ?? <span className="text-slate-500">{BLANK}</span>}
        </span>
        {/* An in-progress (partial) log takes priority over the last-done line. */}
        {session.in_progress_since ? (
          <span className="inline-flex items-center gap-1.5 text-sm text-amber-300">
            <Hourglass size={13} />
            En progreso · empezado {formatLastDone(session.in_progress_since)}
          </span>
        ) : (
          session.last_performed_at && (
            <span className="inline-flex items-center gap-1.5 text-sm text-slate-400">
              <CalendarCheck size={13} className="text-emerald-400" />
              Última vez: {formatLastDone(session.last_performed_at)}
            </span>
          )
        )}
      </button>
    </li>
  )
}

export default SortableTrainingRow
