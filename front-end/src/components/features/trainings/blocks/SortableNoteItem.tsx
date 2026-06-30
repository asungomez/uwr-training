import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Trash2 } from 'lucide-react'

import MoveButtons from './MoveButtons'
import type { NoteDraft } from './TrainingBlocksEditor'

interface SortableNoteItemProps {
  item: NoteDraft
  onChange: (item: NoteDraft) => void
  onRemove: () => void
  canMoveUp: boolean
  canMoveDown: boolean
  onMoveUp: () => void
  onMoveDown: () => void
}

function SortableNoteItem({
  item,
  onChange,
  onRemove,
  canMoveUp,
  canMoveDown,
  onMoveUp,
  onMoveDown,
}: SortableNoteItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`flex items-start gap-2 ${isDragging ? 'z-10 opacity-60' : ''}`}
    >
      {/* Reorder controls: drag handle + move chevrons. Stacked on mobile. */}
      <div className="mt-1 flex flex-col items-center sm:flex-row sm:items-start">
        <button
          type="button"
          {...attributes}
          {...listeners}
          aria-label="Reordenar nota"
          className="cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
        >
          <GripVertical size={14} />
        </button>

        <MoveButtons
          canMoveUp={canMoveUp}
          canMoveDown={canMoveDown}
          onMoveUp={onMoveUp}
          onMoveDown={onMoveDown}
          label="nota"
        />
      </div>

      <textarea
        value={item.text}
        onChange={(event) => onChange({ ...item, text: event.target.value })}
        rows={2}
        placeholder="Nota (p. ej. 10s de descanso, quítate las aletas)…"
        aria-label="Nota"
        className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
      />

      <button
        type="button"
        onClick={onRemove}
        aria-label="Eliminar nota"
        className="mt-1 rounded p-1 text-slate-400 transition-colors hover:bg-red-500/15 hover:text-red-300 focus:ring-2 focus:ring-red-400 focus:outline-none"
      >
        <Trash2 size={14} />
      </button>
    </li>
  )
}

export default SortableNoteItem
