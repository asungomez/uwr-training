import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical } from 'lucide-react'

import type { components } from '@/api/schema'

type CardioTraining = components['schemas']['CardioTrainingResponse']

const BLANK = 'Sin título'

interface SortableCardioRowProps {
  training: CardioTraining
  /** Show the drag handle (admins only, and not while searching). */
  draggable: boolean
  onOpen: () => void
  /** Whether this row is ticked for the multi-session PDF export. */
  selected: boolean
  onToggleSelected: () => void
}

function SortableCardioRow({
  training,
  draggable,
  onOpen,
  selected,
  onToggleSelected,
}: SortableCardioRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: training.id,
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
        aria-label={`Seleccionar ${training.title ?? BLANK}`}
        className="ml-3 size-4 shrink-0 accent-indigo-500"
      />
      {draggable && (
        <button
          type="button"
          {...attributes}
          {...listeners}
          aria-label="Reordenar entrenamiento"
          className="cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
        >
          <GripVertical size={18} />
        </button>
      )}
      <button
        type="button"
        onClick={onOpen}
        className="flex-1 py-4 pr-4 pl-3 text-left font-medium text-slate-100 focus:outline-none"
      >
        {training.title ?? <span className="text-slate-500">{BLANK}</span>}
      </button>
    </li>
  )
}

export default SortableCardioRow
