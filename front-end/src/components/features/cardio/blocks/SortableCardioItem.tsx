import {
  closestCenter,
  DndContext,
  type DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Plus, Trash2 } from 'lucide-react'

import { controlClass } from '@/components/atoms/form/fieldStyles'
import {
  type CardioFormValues,
  type IntervalDraft,
  newEffort,
  newRest,
} from '@/components/features/cardio/cardioFormValues'

import SortableInterval from './SortableInterval'

type ItemDraft = CardioFormValues['items'][number]
type BlockDraft = Extract<ItemDraft, { kind: 'block' }>

interface SortableCardioItemProps {
  item: ItemDraft
  onChange: (item: ItemDraft) => void
  onRemove: () => void
}

/** One entry of a cardio training: a free-text note ("10s descanso" between
 *  blocks) or a block — a round (its intervals) repeated N times with a trailing
 *  rest. The intervals get their own nested DnD context. */
function SortableCardioItem({ item, onChange, onRemove }: SortableCardioItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.id,
  })
  const style = { transform: CSS.Transform.toString(transform), transition }

  const intervalSensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  function updateBlock(changes: Partial<BlockDraft>) {
    if (item.kind !== 'block') return
    onChange({ ...item, ...changes })
  }

  function handleIntervalDragEnd(event: DragEndEvent) {
    if (item.kind !== 'block') return
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = item.intervals.findIndex((i) => i.id === active.id)
    const to = item.intervals.findIndex((i) => i.id === over.id)
    if (from === -1 || to === -1) return
    updateBlock({ intervals: arrayMove(item.intervals, from, to) })
  }

  function updateInterval(updated: IntervalDraft) {
    if (item.kind !== 'block') return
    updateBlock({
      intervals: item.intervals.map((i) => (i.id === updated.id ? updated : i)),
    })
  }

  function removeInterval(id: string) {
    if (item.kind !== 'block') return
    updateBlock({ intervals: item.intervals.filter((i) => i.id !== id) })
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`rounded-lg border border-slate-700 bg-slate-800 ${isDragging ? 'z-10 opacity-60 shadow-xl' : ''}`}
    >
      <div className="flex items-start gap-2 p-3">
        <button
          type="button"
          {...attributes}
          {...listeners}
          aria-label={item.kind === 'block' ? 'Reordenar bloque' : 'Reordenar nota'}
          className="mt-1 cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
        >
          <GripVertical size={18} />
        </button>

        <div className="flex flex-1 flex-col gap-3">
          {item.kind === 'note' ? (
            <textarea
              value={item.text}
              onChange={(event) => onChange({ ...item, text: event.target.value })}
              rows={2}
              placeholder="Nota entre bloques (p. ej. 10s descanso)…"
              aria-label="Nota"
              className={`${controlClass} w-full text-sm`}
            />
          ) : (
            <>
              <div className="flex flex-wrap items-end gap-4">
                <label className="flex flex-col gap-1 text-xs font-medium text-slate-400">
                  Repeticiones del bloque
                  <input
                    value={item.repeats}
                    onChange={(event) => updateBlock({ repeats: event.target.value })}
                    inputMode="numeric"
                    aria-label="Repeticiones del bloque"
                    className={`${controlClass} w-20 py-1.5 text-sm`}
                  />
                </label>
                <label className="flex flex-col gap-1 text-xs font-medium text-slate-400">
                  Descanso final
                  <input
                    value={item.rest}
                    onChange={(event) => updateBlock({ rest: event.target.value })}
                    placeholder="mm:ss"
                    aria-label="Descanso final"
                    className={`${controlClass} w-24 py-1.5 text-sm`}
                  />
                </label>
              </div>

              <DndContext
                sensors={intervalSensors}
                collisionDetection={closestCenter}
                onDragEnd={handleIntervalDragEnd}
              >
                <SortableContext
                  items={item.intervals.map((i) => i.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <ul className="flex flex-col gap-2">
                    {item.intervals.map((interval) => (
                      <SortableInterval
                        key={interval.id}
                        interval={interval}
                        onChange={updateInterval}
                        onRemove={() => removeInterval(interval.id)}
                      />
                    ))}
                  </ul>
                </SortableContext>
              </DndContext>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => updateBlock({ intervals: [...item.intervals, newEffort()] })}
                  className="inline-flex items-center gap-2 rounded-md border border-dashed border-slate-600 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                >
                  <Plus size={14} />
                  Añadir esfuerzo
                </button>
                <button
                  type="button"
                  onClick={() => updateBlock({ intervals: [...item.intervals, newRest()] })}
                  className="inline-flex items-center gap-2 rounded-md border border-dashed border-slate-600 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                >
                  <Plus size={14} />
                  Añadir descanso
                </button>
              </div>
            </>
          )}
        </div>

        <button
          type="button"
          onClick={onRemove}
          aria-label={item.kind === 'block' ? 'Eliminar bloque' : 'Eliminar nota'}
          className="mt-1 rounded p-1 text-slate-400 transition-colors hover:bg-red-500/15 hover:text-red-300 focus:ring-2 focus:ring-red-400 focus:outline-none"
        >
          <Trash2 size={18} />
        </button>
      </div>
    </li>
  )
}

export default SortableCardioItem
