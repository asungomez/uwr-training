import { Plus, X } from 'lucide-react'
import { useState } from 'react'
import { type Control, useFieldArray } from 'react-hook-form'

import { useQuery } from '@/api/client'
import { controlClass, labelClass } from '@/components/atoms/form/fieldStyles'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'

import type { ExerciseFormValues } from './ExerciseForm'

interface GymFacilitiesFieldProps {
  control: Control<ExerciseFormValues>
}

/** Manages an exercise's list of gym facilities (installations). Type a name to get
 *  suggestions from existing facilities; pick one to link it, or just add the typed
 *  text to create a new facility on save. Each added facility is a removable chip. */
function GymFacilitiesField({ control }: GymFacilitiesFieldProps) {
  const { fields, append, remove } = useFieldArray({ control, name: 'gymFacilities' })
  const [draft, setDraft] = useState('')
  const debounced = useDebouncedValue(draft.trim(), 300)

  const { data } = useQuery(
    '/gym-facilities',
    { params: { query: { page: 1, page_size: 8, search: debounced } } },
    { keepPreviousData: true },
  )

  // Case-insensitive set of names already added, to hide them from suggestions and
  // block duplicate adds.
  const addedNames = new Set(fields.map((field) => field.name.toLowerCase()))
  const suggestions = (data?.items ?? []).filter(
    (facility) => !addedNames.has(facility.name.toLowerCase()),
  )

  function add(name: string) {
    const trimmed = name.trim()
    if (!trimmed || addedNames.has(trimmed.toLowerCase())) {
      setDraft('')
      return
    }
    append({ name: trimmed })
    setDraft('')
  }

  return (
    <div className="flex flex-col gap-2">
      <span className={labelClass}>Instalaciones</span>

      {fields.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {fields.map((field, index) => (
            <li
              key={field.id}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-600 bg-slate-800 py-1 pr-1 pl-3 text-sm text-slate-100"
            >
              {field.name}
              <button
                type="button"
                onClick={() => remove(index)}
                aria-label={`Quitar ${field.name}`}
                className="rounded-full p-0.5 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <X size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              // Don't submit the whole form; add the facility instead.
              event.preventDefault()
              add(draft)
            }
          }}
          placeholder="Añadir instalación (p. ej. Máquina de remo)…"
          aria-label="Instalación"
          className={`${controlClass} flex-1 text-sm`}
        />
        <button
          type="button"
          onClick={() => add(draft)}
          disabled={!draft.trim()}
          aria-label="Añadir instalación"
          className="inline-flex shrink-0 items-center justify-center rounded-md border border-slate-600 px-3 text-slate-200 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus size={16} />
        </button>
      </div>

      {debounced && suggestions.length > 0 && (
        <ul className="flex flex-col gap-1 rounded-md border border-slate-700 bg-slate-900 p-1">
          {suggestions.map((facility) => (
            <li key={facility.id}>
              <button
                type="button"
                onClick={() => add(facility.name)}
                className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm text-slate-200 transition-colors hover:bg-slate-700 focus:bg-slate-700 focus:outline-none"
              >
                <Plus size={14} className="shrink-0 text-slate-400" />
                {facility.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default GymFacilitiesField
