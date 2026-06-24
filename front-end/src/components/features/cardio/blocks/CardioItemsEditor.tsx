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
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { Plus } from 'lucide-react'

import {
  type CardioFormValues,
  newBlock,
  newNote,
} from '@/components/features/cardio/cardioFormValues'

import SortableCardioItem from './SortableCardioItem'

type ItemDraft = CardioFormValues['items'][number]

interface CardioItemsEditorProps {
  value: ItemDraft[]
  onChange: (items: ItemDraft[]) => void
}

/** Drag-and-drop editor for a cardio training's ordered items (blocks and notes).
 *  `value`/`onChange` are the form-owned list. */
function CardioItemsEditor({ value: items, onChange }: CardioItemsEditorProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = items.findIndex((i) => i.id === active.id)
    const to = items.findIndex((i) => i.id === over.id)
    if (from === -1 || to === -1) return
    onChange(arrayMove(items, from, to))
  }

  function updateItem(updated: ItemDraft) {
    onChange(items.map((i) => (i.id === updated.id ? updated : i)))
  }

  function removeItem(id: string) {
    onChange(items.filter((i) => i.id !== id))
  }

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-lg font-semibold text-slate-100">Bloques</h3>

      {items.length === 0 && <p className="text-sm text-slate-500">Todavía no hay bloques.</p>}

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          <ul className="flex flex-col gap-3">
            {items.map((item) => (
              <SortableCardioItem
                key={item.id}
                item={item}
                onChange={updateItem}
                onRemove={() => removeItem(item.id)}
              />
            ))}
          </ul>
        </SortableContext>
      </DndContext>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onChange([...items, newBlock()])}
          className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-4 py-2 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <Plus size={16} />
          Añadir bloque
        </button>
        <button
          type="button"
          onClick={() => onChange([...items, newNote()])}
          className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-4 py-2 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <Plus size={16} />
          Añadir nota
        </button>
      </div>
    </div>
  )
}

export default CardioItemsEditor
