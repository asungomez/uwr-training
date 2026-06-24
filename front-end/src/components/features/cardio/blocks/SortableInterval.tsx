import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Trash2 } from 'lucide-react'

import { controlClass } from '@/components/atoms/form/fieldStyles'
import type { IntervalDraft } from '@/components/features/cardio/cardioFormValues'

interface SortableIntervalProps {
  interval: IntervalDraft
  onChange: (interval: IntervalDraft) => void
  onRemove: () => void
}

/** One step of a block's round: an effort (duration + intensity %) or a rest
 *  (duration only). Reorderable within its block. */
function SortableInterval({ interval, onChange, onRemove }: SortableIntervalProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: interval.id,
  })
  const style = { transform: CSS.Transform.toString(transform), transition }
  const isRest = interval.kind === 'rest'

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-2 ${isDragging ? 'z-10 opacity-60' : ''}`}
    >
      <button
        type="button"
        {...attributes}
        {...listeners}
        aria-label="Reordenar intervalo"
        className="cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
      >
        <GripVertical size={14} />
      </button>

      <span
        className={`w-16 shrink-0 text-xs font-medium ${isRest ? 'text-slate-400' : 'text-indigo-300'}`}
      >
        {isRest ? 'Descanso' : 'Esfuerzo'}
      </span>

      <input
        value={interval.time}
        onChange={(event) => onChange({ ...interval, time: event.target.value })}
        placeholder="mm:ss"
        inputMode="text"
        aria-label="Duración"
        className={`${controlClass} w-24 py-1.5 text-sm`}
      />

      {interval.kind === 'effort' && (
        <div className="flex items-center gap-1">
          <input
            value={interval.intensity}
            onChange={(event) => onChange({ ...interval, intensity: event.target.value })}
            placeholder="80"
            inputMode="numeric"
            aria-label="Intensidad"
            className={`${controlClass} w-16 py-1.5 text-sm`}
          />
          <span className="text-sm text-slate-400">%</span>
        </div>
      )}

      <button
        type="button"
        onClick={onRemove}
        aria-label="Eliminar intervalo"
        className="ml-auto rounded p-1 text-slate-400 transition-colors hover:bg-red-500/15 hover:text-red-300 focus:ring-2 focus:ring-red-400 focus:outline-none"
      >
        <Trash2 size={14} />
      </button>
    </li>
  )
}

export default SortableInterval
