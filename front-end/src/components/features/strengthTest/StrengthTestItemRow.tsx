import { Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { type Control, type UseFormRegister, type UseFormSetValue, useWatch } from 'react-hook-form'

import { useQuery } from '@/api/client'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import SearchInput from '@/components/molecules/SearchInput'
import type { StrengthTestFormInput } from '@/components/features/strengthTest/strengthTestFormValues'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'

interface StrengthTestItemRowProps {
  index: number
  control: Control<StrengthTestFormInput>
  register: UseFormRegister<StrengthTestFormInput>
  setValue: UseFormSetValue<StrengthTestFormInput>
  onRemove: () => void
}

/** One strength-test row: a gym exercise (chosen via search) and its multiplier. */
function StrengthTestItemRow({
  index,
  control,
  register,
  setValue,
  onRemove,
}: StrengthTestItemRowProps) {
  const exerciseId = useWatch({ control, name: `items.${index}.exerciseId` })
  const exerciseName = useWatch({ control, name: `items.${index}.exerciseName` })

  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search.trim(), 300)
  const { data } = useQuery(
    '/exercises',
    // Skip once an exercise is picked (the search UI is hidden then). The strength
    // test guides gym training, so restrict the search to gym exercises.
    exerciseId
      ? null
      : { params: { query: { page: 1, page_size: 8, search: debouncedSearch, type: 'gym' } } },
    { keepPreviousData: true },
  )
  const results = data?.items ?? []

  function pick(id: string, name: string) {
    setValue(`items.${index}.exerciseId`, id)
    setValue(`items.${index}.exerciseName`, name)
    setSearch('')
  }

  // Keep the id/name in the form even though they're not rendered as inputs.
  register(`items.${index}.exerciseId`)
  register(`items.${index}.exerciseName`)

  return (
    <li className="flex items-start gap-3 rounded-md border border-slate-700 bg-slate-900/50 p-3">
      <div className="flex flex-1 flex-col gap-2">
        {exerciseId ? (
          <span className="font-medium text-slate-100">{exerciseName}</span>
        ) : (
          <>
            <SearchInput value={search} onChange={setSearch} placeholder="Buscar ejercicio…" />
            {debouncedSearch && results.length > 0 && (
              <ul className="flex flex-col gap-1 rounded-md border border-slate-700 bg-slate-900 p-1">
                {results.map((exercise) => (
                  <li key={exercise.id}>
                    <button
                      type="button"
                      onClick={() => pick(exercise.id, exercise.name)}
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
              <p className="text-sm text-slate-500">No hay ejercicios de gimnasio que coincidan.</p>
            )}
          </>
        )}
      </div>

      <label className="flex w-28 flex-col gap-1 text-xs font-medium text-slate-400">
        Multiplicador
        <input
          {...register(`items.${index}.multiplier`)}
          inputMode="decimal"
          aria-label="Multiplicador"
          className={`${controlClass} w-full py-1.5 text-sm`}
        />
      </label>

      <button
        type="button"
        onClick={onRemove}
        aria-label="Eliminar ejercicio"
        className="mt-1 rounded p-1 text-slate-400 transition-colors hover:bg-red-500/15 hover:text-red-300 focus:ring-2 focus:ring-red-400 focus:outline-none"
      >
        <Trash2 size={16} />
      </button>
    </li>
  )
}

export default StrengthTestItemRow
