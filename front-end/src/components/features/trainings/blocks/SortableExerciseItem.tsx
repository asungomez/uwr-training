import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { useQuery } from '@/api/client'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import SearchInput from '@/components/molecules/SearchInput'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'

import type { components } from '@/api/schema'

import type { SeriesDraft } from './TrainingBlocksEditor'

type ExerciseType = components['schemas']['ExerciseType']

interface SortableExerciseItemProps {
  item: SeriesDraft
  onChange: (item: SeriesDraft) => void
  onRemove: () => void
  /** Restrict the search to this exercise type (null = no restriction). */
  exerciseType: ExerciseType | null
}

interface FieldProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  inputMode?: 'numeric' | 'text' | 'decimal'
}

function SeriesField({ label, value, onChange, placeholder, inputMode = 'numeric' }: FieldProps) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-slate-400">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        inputMode={inputMode}
        aria-label={label}
        className={`${controlClass} py-1.5 text-sm`}
      />
    </label>
  )
}

/** A series item: an exercise (chosen via search) plus an all-optional
 *  prescription (sets/reps/time/distance/effort) and free-text notes. */
function SortableExerciseItem({
  item,
  onChange,
  onRemove,
  exerciseType,
}: SortableExerciseItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.id,
  })
  const style = { transform: CSS.Transform.toString(transform), transition }

  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search.trim(), 300)
  const { data } = useQuery(
    '/exercises',
    // Skip fetching once an exercise is picked (the search UI is hidden then).
    // Filter by the training category's exercise type when there is one.
    item.exerciseId
      ? null
      : {
          params: {
            query: {
              page: 1,
              page_size: 8,
              search: debouncedSearch,
              ...(exerciseType ? { type: exerciseType } : {}),
            },
          },
        },
    { keepPreviousData: true },
  )
  const results = data?.items ?? []

  // The load field only applies to exercises that are part of the strength test
  // (its result is what the % is taken from). SWR dedupes this across all rows.
  const { data: strengthTest } = useQuery('/strength-test', {})
  const isTested = strengthTest?.items.some((sti) => sti.exercise_id === item.exerciseId) ?? false

  function pickExercise(exerciseId: string, exerciseName: string) {
    onChange({ ...item, exerciseId, exerciseName })
    setSearch('')
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`flex items-start gap-2 rounded-md border border-slate-700 bg-slate-900/40 p-2 ${isDragging ? 'z-10 opacity-60' : ''}`}
    >
      {/* Drag handle — scoped to this sub-block's items. */}
      <button
        type="button"
        {...attributes}
        {...listeners}
        aria-label="Reordenar ejercicio"
        className="mt-1 cursor-grab touch-none rounded p-1 text-slate-500 transition-colors hover:bg-slate-700 hover:text-slate-200 focus:ring-2 focus:ring-indigo-400 focus:outline-none active:cursor-grabbing"
      >
        <GripVertical size={14} />
      </button>

      <div className="flex flex-1 flex-col gap-2">
        {item.exerciseId ? (
          <span className="font-medium text-slate-100">{item.exerciseName}</span>
        ) : (
          <>
            <SearchInput value={search} onChange={setSearch} placeholder="Buscar ejercicio…" />
            {debouncedSearch && results.length > 0 && (
              <ul className="flex flex-col gap-1 rounded-md border border-slate-700 bg-slate-900 p-1">
                {results.map((exercise) => (
                  <li key={exercise.id}>
                    <button
                      type="button"
                      onClick={() => pickExercise(exercise.id, exercise.name)}
                      className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm text-slate-200 transition-colors hover:bg-slate-700 focus:bg-slate-700 focus:outline-none"
                    >
                      <Plus size={14} className="shrink-0 text-slate-400" />
                      {exercise.name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {debouncedSearch && results.length === 0 && (
              <p className="text-sm text-slate-500">No hay ejercicios que coincidan.</p>
            )}
          </>
        )}

        {item.exerciseId && (
          <>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <SeriesField
                label="Series"
                value={item.sets}
                onChange={(value) => onChange({ ...item, sets: value })}
              />
              <SeriesField
                label="Repeticiones por serie"
                value={item.reps}
                onChange={(value) => onChange({ ...item, reps: value })}
              />
              <SeriesField
                label="Tiempo por serie"
                value={item.time}
                onChange={(value) => onChange({ ...item, time: value })}
                placeholder="mm:ss"
                inputMode="text"
              />
              <SeriesField
                label="Distancia"
                value={item.distance}
                onChange={(value) => onChange({ ...item, distance: value })}
                placeholder="metros"
                inputMode="decimal"
              />
              <SeriesField
                label="Intensidad"
                value={item.effort}
                onChange={(value) => onChange({ ...item, effort: value })}
                inputMode="text"
              />
              {isTested && (
                <SeriesField
                  label="Carga (%)"
                  value={item.load}
                  onChange={(value) => onChange({ ...item, load: value })}
                  placeholder="% de la prueba"
                  inputMode="decimal"
                />
              )}
            </div>
            <textarea
              value={item.notes}
              onChange={(event) => onChange({ ...item, notes: event.target.value })}
              rows={2}
              placeholder="Notas…"
              aria-label="Notas del ejercicio"
              className={`${controlClass} w-full text-sm`}
            />
          </>
        )}
      </div>

      <button
        type="button"
        onClick={onRemove}
        aria-label="Eliminar ejercicio"
        className="mt-1 rounded p-1 text-slate-400 transition-colors hover:bg-red-500/15 hover:text-red-300 focus:ring-2 focus:ring-red-400 focus:outline-none"
      >
        <Trash2 size={14} />
      </button>
    </li>
  )
}

export default SortableExerciseItem
