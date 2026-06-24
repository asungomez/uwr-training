import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { ChevronDown, ChevronRight, GripVertical, Trash2 } from 'lucide-react'

import type { BlockDraft } from './TrainingBlocksEditor'

interface SortableBlockCardProps {
  block: BlockDraft
  collapsed: boolean
  onToggleCollapsed: () => void
  onRename: (name: string) => void
  onRemove: () => void
}

function SortableBlockCard({
  block,
  collapsed,
  onToggleCollapsed,
  onRename,
  onRemove,
}: SortableBlockCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`rounded-lg border border-slate-700 bg-slate-800 ${isDragging ? 'z-10 opacity-60 shadow-xl' : ''}`}
    >
      <div className="flex items-center gap-2 p-3">
        {/* Drag handle — only this initiates dragging, so the name input stays usable. */}
        <button
          type="button"
          {...attributes}
          {...listeners}
          aria-label="Reordenar bloque"
          className="cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
        >
          <GripVertical size={18} />
        </button>

        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? 'Expandir bloque' : 'Colapsar bloque'}
          aria-expanded={!collapsed}
          className="rounded p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronDown size={18} />}
        </button>

        <input
          value={block.name}
          onChange={(event) => onRename(event.target.value)}
          placeholder="Nombre del bloque (p. ej. Calentamiento)"
          aria-label="Nombre del bloque"
          className="flex-1 rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
        />

        <button
          type="button"
          onClick={onRemove}
          aria-label="Eliminar bloque"
          className="rounded p-1 text-slate-400 transition-colors hover:bg-red-500/15 hover:text-red-300 focus:ring-2 focus:ring-red-400 focus:outline-none"
        >
          <Trash2 size={18} />
        </button>
      </div>

      {!collapsed && (
        <div className="border-t border-slate-700 px-4 py-3">
          <p className="text-sm text-slate-500">
            Los sub-bloques y series se añadirán aquí próximamente.
          </p>
        </div>
      )}
    </li>
  )
}

export default SortableBlockCard
