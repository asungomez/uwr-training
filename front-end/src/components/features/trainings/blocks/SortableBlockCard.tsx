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
import { ChevronDown, ChevronRight, Copy, GripVertical, Plus, Trash2 } from 'lucide-react'

import type { components } from '@/api/schema'

import { cloneSubBlock } from './cloneDrafts'
import MoveButtons from './MoveButtons'
import SortableSubBlockCard from './SortableSubBlockCard'
import type { BlockDraft, SubBlockDraft } from './TrainingBlocksEditor'

type ExerciseType = components['schemas']['ExerciseType']

interface SortableBlockCardProps {
  block: BlockDraft
  collapsed: boolean
  onToggleCollapsed: () => void
  onChange: (block: BlockDraft) => void
  onRemove: () => void
  /** Insert a copy of this whole block right below it. */
  onCopy: () => void
  exerciseType: ExerciseType | null
  canMoveUp: boolean
  canMoveDown: boolean
  onMoveUp: () => void
  onMoveDown: () => void
}

function newSubBlock(): SubBlockDraft {
  return { id: crypto.randomUUID(), name: '', notes: '', items: [] }
}

function SortableBlockCard({
  block,
  collapsed,
  onToggleCollapsed,
  onChange,
  onRemove,
  onCopy,
  exerciseType,
  canMoveUp,
  canMoveDown,
  onMoveUp,
  onMoveDown,
}: SortableBlockCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  })

  // Sub-blocks get their OWN DnD context, so dragging one reorders only within this
  // block — drags never cross into another block.
  const subSensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  function handleSubDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = block.subBlocks.findIndex((s) => s.id === active.id)
    const to = block.subBlocks.findIndex((s) => s.id === over.id)
    if (from === -1 || to === -1) return
    onChange({ ...block, subBlocks: arrayMove(block.subBlocks, from, to) })
  }

  function addSubBlock() {
    onChange({ ...block, subBlocks: [...block.subBlocks, newSubBlock()] })
  }

  function updateSubBlock(updated: SubBlockDraft) {
    onChange({
      ...block,
      subBlocks: block.subBlocks.map((s) => (s.id === updated.id ? updated : s)),
    })
  }

  function removeSubBlock(id: string) {
    onChange({ ...block, subBlocks: block.subBlocks.filter((s) => s.id !== id) })
  }

  function copySubBlock(id: string) {
    const index = block.subBlocks.findIndex((s) => s.id === id)
    const original = block.subBlocks[index]
    if (!original) return
    const copy = cloneSubBlock(original)
    const subBlocks = [...block.subBlocks]
    subBlocks.splice(index + 1, 0, copy)
    onChange({ ...block, subBlocks })
  }

  /** Move a sub-block one position up (-1) or down (+1) within the block. */
  function moveSubBlock(index: number, delta: number) {
    const to = index + delta
    if (to < 0 || to >= block.subBlocks.length) return
    onChange({ ...block, subBlocks: arrayMove(block.subBlocks, index, to) })
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`rounded-lg border border-slate-700 bg-slate-800 ${isDragging ? 'z-10 opacity-60 shadow-xl' : ''}`}
    >
      <div className="flex items-center gap-2 p-3">
        {/* Reorder controls: drag handle + move chevrons. Stacked on mobile. */}
        <div className="flex flex-col items-center sm:flex-row sm:items-center">
          <button
            type="button"
            {...attributes}
            {...listeners}
            aria-label="Reordenar bloque"
            className="cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
          >
            <GripVertical size={18} />
          </button>

          <MoveButtons
            canMoveUp={canMoveUp}
            canMoveDown={canMoveDown}
            onMoveUp={onMoveUp}
            onMoveDown={onMoveDown}
            label="bloque"
          />
        </div>

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
          onChange={(event) => onChange({ ...block, name: event.target.value })}
          placeholder="Nombre del bloque (p. ej. Calentamiento)"
          aria-label="Nombre del bloque"
          className="flex-1 rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
        />

        <button
          type="button"
          onClick={onCopy}
          aria-label="Copiar bloque"
          className="rounded p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <Copy size={18} />
        </button>

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
        <div className="flex flex-col gap-3 border-t border-slate-700 px-4 py-3">
          {block.subBlocks.length === 0 && (
            <p className="text-sm text-slate-500">Todavía no hay sub-bloques.</p>
          )}

          <DndContext
            sensors={subSensors}
            collisionDetection={closestCenter}
            onDragEnd={handleSubDragEnd}
          >
            <SortableContext
              items={block.subBlocks.map((s) => s.id)}
              strategy={verticalListSortingStrategy}
            >
              <ul className="flex flex-col gap-2">
                {block.subBlocks.map((subBlock, index) => (
                  <SortableSubBlockCard
                    key={subBlock.id}
                    subBlock={subBlock}
                    onChange={updateSubBlock}
                    onRemove={() => removeSubBlock(subBlock.id)}
                    onCopy={() => copySubBlock(subBlock.id)}
                    exerciseType={exerciseType}
                    canMoveUp={index > 0}
                    canMoveDown={index < block.subBlocks.length - 1}
                    onMoveUp={() => moveSubBlock(index, -1)}
                    onMoveDown={() => moveSubBlock(index, 1)}
                  />
                ))}
              </ul>
            </SortableContext>
          </DndContext>

          <button
            type="button"
            onClick={addSubBlock}
            className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Plus size={16} />
            Añadir sub-bloque
          </button>
        </div>
      )}
    </li>
  )
}

export default SortableBlockCard
