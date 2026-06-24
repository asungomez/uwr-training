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
import { ChevronsDownUp, ChevronsUpDown, Plus } from 'lucide-react'
import { useState } from 'react'

import type { components } from '@/api/schema'

import SortableBlockCard from './SortableBlockCard'

type ExerciseType = components['schemas']['ExerciseType']

export interface NoteDraft {
  /** Stable client-side id (not the eventual DB id) for list keys + DnD. */
  id: string
  kind: 'note'
  text: string
}

export interface SeriesDraft {
  /** Stable client-side id (not the eventual DB id) for list keys + DnD. */
  id: string
  kind: 'series'
  exerciseId: string
  exerciseName: string
  sets: string
  reps: string
  // mm:ss in the form; converted to/from duration_seconds at the API boundary.
  time: string
  distance: string
  effort: string
  notes: string
}

/** A sub-block's items are an ordered mix of free-text notes and exercise series. */
export type ItemDraft = NoteDraft | SeriesDraft

export interface SubBlockDraft {
  /** Stable client-side id (not the eventual DB id) for list keys + DnD. */
  id: string
  name: string
  notes: string
  items: ItemDraft[]
}

export interface BlockDraft {
  /** Stable client-side id (not the eventual DB id) for list keys + DnD. */
  id: string
  name: string
  subBlocks: SubBlockDraft[]
}

function newBlock(): BlockDraft {
  return { id: crypto.randomUUID(), name: '', subBlocks: [] }
}

interface TrainingBlocksEditorProps {
  value: BlockDraft[]
  onChange: (blocks: BlockDraft[]) => void
  /** Restrict the exercise picker to this type (null = no restriction, e.g. cardio). */
  exerciseType: ExerciseType | null
}

/** Drag-and-drop editor for a training's ordered blocks. `value`/`onChange` are
 *  the form-owned block list; collapse state is local UI. */
function TrainingBlocksEditor({
  value: blocks,
  onChange,
  exerciseType,
}: TrainingBlocksEditorProps) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const anyExpanded = blocks.some((b) => !collapsed.has(b.id))
  const anyCollapsed = blocks.some((b) => collapsed.has(b.id))

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = blocks.findIndex((b) => b.id === active.id)
    const to = blocks.findIndex((b) => b.id === over.id)
    if (from === -1 || to === -1) return
    onChange(arrayMove(blocks, from, to))
  }

  function addBlock() {
    onChange([...blocks, newBlock()])
  }

  function updateBlock(updated: BlockDraft) {
    onChange(blocks.map((b) => (b.id === updated.id ? updated : b)))
  }

  function removeBlock(id: string) {
    onChange(blocks.filter((b) => b.id !== id))
    setCollapsed((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }

  function toggleCollapsed(id: string) {
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function collapseAll() {
    setCollapsed(new Set(blocks.map((b) => b.id)))
  }

  function expandAll() {
    setCollapsed(new Set())
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-100">Bloques</h3>
        <div className="flex items-center gap-1">
          {anyCollapsed && (
            <button
              type="button"
              onClick={expandAll}
              className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              <ChevronsUpDown size={16} />
              Expandir todo
            </button>
          )}
          {anyExpanded && (
            <button
              type="button"
              onClick={collapseAll}
              className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              <ChevronsDownUp size={16} />
              Colapsar todo
            </button>
          )}
        </div>
      </div>

      {blocks.length === 0 && <p className="text-sm text-slate-500">Todavía no hay bloques.</p>}

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
          <ul className="flex flex-col gap-3">
            {blocks.map((block) => (
              <SortableBlockCard
                key={block.id}
                block={block}
                collapsed={collapsed.has(block.id)}
                onToggleCollapsed={() => toggleCollapsed(block.id)}
                onChange={updateBlock}
                onRemove={() => removeBlock(block.id)}
                exerciseType={exerciseType}
              />
            ))}
          </ul>
        </SortableContext>
      </DndContext>

      <button
        type="button"
        onClick={addBlock}
        className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-4 py-2 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      >
        <Plus size={16} />
        Añadir bloque
      </button>
    </div>
  )
}

export default TrainingBlocksEditor
