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

import type { components } from '@/api/schema'

import SortableExerciseItem from './SortableExerciseItem'
import SortableNoteItem from './SortableNoteItem'
import type { ItemDraft, SeriesDraft, SubBlockDraft } from './TrainingBlocksEditor'

type ExerciseType = components['schemas']['ExerciseType']

interface SortableSubBlockCardProps {
  subBlock: SubBlockDraft
  onChange: (subBlock: SubBlockDraft) => void
  onRemove: () => void
  exerciseType: ExerciseType | null
}

function newNote(): ItemDraft {
  return { id: crypto.randomUUID(), kind: 'note', text: '' }
}

function newSeries(): SeriesDraft {
  return {
    id: crypto.randomUUID(),
    kind: 'series',
    exerciseId: '',
    exerciseName: '',
    sets: '',
    reps: '',
    time: '',
    distance: '',
    effort: '',
    load: '',
    notes: '',
  }
}

function SortableSubBlockCard({
  subBlock,
  onChange,
  onRemove,
  exerciseType,
}: SortableSubBlockCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: subBlock.id,
  })

  // Items get their OWN DnD context, so dragging a note reorders only within this
  // sub-block — never across sub-blocks or blocks.
  const itemSensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  function handleItemDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = subBlock.items.findIndex((i) => i.id === active.id)
    const to = subBlock.items.findIndex((i) => i.id === over.id)
    if (from === -1 || to === -1) return
    onChange({ ...subBlock, items: arrayMove(subBlock.items, from, to) })
  }

  function addNote() {
    onChange({ ...subBlock, items: [...subBlock.items, newNote()] })
  }

  function addSeries() {
    onChange({ ...subBlock, items: [...subBlock.items, newSeries()] })
  }

  function updateItem(updated: ItemDraft) {
    onChange({
      ...subBlock,
      items: subBlock.items.map((item) => (item.id === updated.id ? updated : item)),
    })
  }

  function removeItem(id: string) {
    onChange({ ...subBlock, items: subBlock.items.filter((item) => item.id !== id) })
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

          {/* Items: a mix of notes and exercise series, reorderable within this sub-block. */}
          {subBlock.items.length > 0 && (
            <DndContext
              sensors={itemSensors}
              collisionDetection={closestCenter}
              onDragEnd={handleItemDragEnd}
            >
              <SortableContext
                items={subBlock.items.map((i) => i.id)}
                strategy={verticalListSortingStrategy}
              >
                <ul className="flex flex-col gap-2">
                  {subBlock.items.map((item) =>
                    item.kind === 'series' ? (
                      <SortableExerciseItem
                        key={item.id}
                        item={item}
                        onChange={updateItem}
                        onRemove={() => removeItem(item.id)}
                        exerciseType={exerciseType}
                      />
                    ) : (
                      <SortableNoteItem
                        key={item.id}
                        item={item}
                        onChange={updateItem}
                        onRemove={() => removeItem(item.id)}
                      />
                    ),
                  )}
                </ul>
              </SortableContext>
            </DndContext>
          )}

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={addNote}
              className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              <Plus size={14} />
              Añadir nota
            </button>
            <button
              type="button"
              onClick={addSeries}
              className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              <Plus size={14} />
              Añadir ejercicio
            </button>
          </div>
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
