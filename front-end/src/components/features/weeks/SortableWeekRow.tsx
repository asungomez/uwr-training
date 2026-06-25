import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical } from 'lucide-react'

import type { components } from '@/api/schema'

import { PhaseBadge } from './PhaseBadge'
import { requirementLabel } from './requirementLink'
import WeekStatusIcon from './WeekStatusIcon'

type Week = components['schemas']['WeekResponse']

interface SortableWeekRowProps {
  week: Week
  /** Show the drag handle (admins only, and not while searching). */
  draggable: boolean
  onOpen: () => void
}

function SortableWeekRow({ week, draggable, onOpen }: SortableWeekRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: week.id,
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
          aria-label="Reordenar semana"
          className="cursor-grab touch-none rounded p-1 pl-3 text-slate-500 transition-colors hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
        >
          <GripVertical size={18} />
        </button>
      )}
      <button
        type="button"
        onClick={onOpen}
        className={`flex flex-1 items-start justify-between gap-3 py-4 pr-4 text-left ${draggable ? '' : 'pl-4'}`}
      >
        <span className="flex min-w-0 flex-col gap-1">
          <span className="flex items-center gap-2 font-medium text-slate-100">
            <WeekStatusIcon requirements={week.requirements} size={16} />
            {week.name}
          </span>
          {week.recommended_date && (
            <span className="text-sm text-slate-400">{week.recommended_date}</span>
          )}
          {week.requirements.length > 0 && (
            <span className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm text-slate-400">
              {week.requirements.map((req) => {
                const complete = req.completed >= req.count
                return (
                  <span key={req.id}>
                    {requirementLabel(req.category, req.subtype)}{' '}
                    <span className={complete ? 'text-emerald-300' : 'text-slate-200'}>
                      {req.completed}/{req.count}
                    </span>
                  </span>
                )
              })}
            </span>
          )}
        </span>
        <PhaseBadge phase={week.phase} />
      </button>
    </li>
  )
}

export default SortableWeekRow
