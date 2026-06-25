import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { CalendarCheck, GripVertical } from 'lucide-react'

import type { components } from '@/api/schema'

type TrainingSession = components['schemas']['TrainingSessionResponse']

const BLANK = 'Sin título'

function formatLastDone(value: string): string {
  return new Date(value).toLocaleDateString('es-ES', { dateStyle: 'long' })
}

interface SortableTrainingRowProps {
  session: TrainingSession
  /** Show the drag handle (admins only, and not while searching). */
  draggable: boolean
  onOpen: () => void
}

function SortableTrainingRow({ session, draggable, onOpen }: SortableTrainingRowProps) {
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
      {draggable && (
        <button
          type="button"
          {...attributes}
          {...listeners}
          aria-label="Reordenar entrenamiento"
          className="cursor-grab touch-none rounded p-1 pl-3 text-slate-500 transition-colors hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
        >
          <GripVertical size={18} />
        </button>
      )}
      <button
        type="button"
        onClick={onOpen}
        className={`flex flex-1 flex-col gap-0.5 py-4 pr-4 text-left focus:outline-none ${draggable ? '' : 'pl-4'}`}
      >
        <span className="font-medium text-slate-100">
          {session.title ?? <span className="text-slate-500">{BLANK}</span>}
        </span>
        {session.last_performed_at && (
          <span className="inline-flex items-center gap-1.5 text-sm text-slate-400">
            <CalendarCheck size={13} className="text-emerald-400" />
            Última vez: {formatLastDone(session.last_performed_at)}
          </span>
        )}
      </button>
    </li>
  )
}

export default SortableTrainingRow
