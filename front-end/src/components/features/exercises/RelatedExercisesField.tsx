import { Plus, X } from 'lucide-react'
import { useState } from 'react'
import { type Control, type UseFormRegister, useFieldArray } from 'react-hook-form'

import { useQuery } from '@/api/client'
import { labelClass } from '@/components/atoms/form/fieldStyles'
import SearchInput from '@/components/molecules/SearchInput'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'

import type { ExerciseFormValues } from './ExerciseForm'

interface RelatedExercisesFieldProps {
  control: Control<ExerciseFormValues>
  register: UseFormRegister<ExerciseFormValues>
  /** Exclude this exercise from search results (can't relate to itself). */
  excludeExerciseId?: string | undefined
}

/** Manages an exercise's list of alternative/related exercises, each with a note.
 *  A search bar finds exercises to add; each added row gets an editable note. */
function RelatedExercisesField({
  control,
  register,
  excludeExerciseId,
}: RelatedExercisesFieldProps) {
  const { fields, append, remove } = useFieldArray({ control, name: 'relatedExercises' })
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  const { data } = useQuery(
    '/exercises',
    { params: { query: { page: 1, page_size: 8, search: debouncedSearch } } },
    { keepPreviousData: true },
  )

  // Hide already-added exercises and the exercise being edited from the results.
  const addedIds = new Set(fields.map((field) => field.exerciseId))
  const results = (data?.items ?? []).filter(
    (exercise) => exercise.id !== excludeExerciseId && !addedIds.has(exercise.id),
  )

  function add(exerciseId: string, exerciseName: string) {
    append({ exerciseId, exerciseName, note: '' })
    setSearch('')
  }

  return (
    <div className="flex flex-col gap-2">
      <span className={labelClass}>Ejercicios relacionados</span>

      {fields.length > 0 && (
        <ul className="flex flex-col gap-2">
          {fields.map((field, index) => (
            <li
              key={field.id}
              className="flex flex-col gap-2 rounded-md border border-slate-700 bg-slate-900/50 p-3"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-slate-100">{field.exerciseName}</span>
                <button
                  type="button"
                  onClick={() => remove(index)}
                  aria-label={`Quitar ${field.exerciseName}`}
                  className="rounded p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                >
                  <X size={16} />
                </button>
              </div>
              <textarea
                {...register(`relatedExercises.${index}.note`)}
                rows={2}
                placeholder="Nota (cuándo o por qué usar esta alternativa)…"
                className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
              />
            </li>
          ))}
        </ul>
      )}

      <SearchInput
        value={search}
        onChange={setSearch}
        placeholder="Buscar ejercicio a relacionar…"
      />

      {debouncedSearch && results.length > 0 && (
        <ul className="flex flex-col gap-1 rounded-md border border-slate-700 bg-slate-900 p-1">
          {results.map((exercise) => (
            <li key={exercise.id}>
              <button
                type="button"
                onClick={() => add(exercise.id, exercise.name)}
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
    </div>
  )
}

export default RelatedExercisesField
