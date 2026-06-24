import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Trash2 } from 'lucide-react'

import type { SubBlockDraft } from './TrainingBlocksEditor'

interface SortableSubBlockCardProps {
  subBlock: SubBlockDraft
  onChange: (subBlock: SubBlockDraft) => void
  onRemove: () => void
}

function SortableSubBlockCard({ subBlock, onChange, onRemove }: SortableSubBlockCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: subBlock.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`rounded-md border border-slate-700 bg-slate-900/50 ${isDragging ? 'z-10 opacity-60 shadow-lg' : ''}`}
    >
      <div className="flex items-start gap-2 p-3">
        {/* Drag handle — only this initiates dragging, scoped to this block's sub-blocks. */}
        <button
          type="button"
          {...attributes}
          {...listeners}
          aria-label="Reordenar sub-bloque"
          className="mt-1 cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
        >
          <GripVertical size={16} />
        </button>

        <div className="flex flex-1 flex-col gap-2">
          <input
            value={subBlock.name}
            onChange={(event) => onChange({ ...subBlock, name: event.target.value })}
            placeholder="Nombre del sub-bloque (p. ej. Preparación)"
            aria-label="Nombre del sub-bloque"
            className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          />
          <textarea
            value={subBlock.notes}
            onChange={(event) => onChange({ ...subBlock, notes: event.target.value })}
            rows={2}
            placeholder="Notas (p. ej. Repetir 3 veces, hacer con aletas)…"
            aria-label="Notas del sub-bloque"
            className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          />
        </div>

        <button
          type="button"
          onClick={onRemove}
          aria-label="Eliminar sub-bloque"
          className="mt-1 rounded p-1 text-slate-400 transition-colors hover:bg-red-500/15 hover:text-red-300 focus:ring-2 focus:ring-red-400 focus:outline-none"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </li>
  )
}

export default SortableSubBlockCard
