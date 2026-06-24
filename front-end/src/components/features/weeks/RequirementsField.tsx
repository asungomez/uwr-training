import { Plus, Trash2 } from 'lucide-react'
import {
  type Control,
  type UseFormRegister,
  type UseFormSetValue,
  useFieldArray,
  useWatch,
} from 'react-hook-form'

import { controlClass, labelClass } from '@/components/atoms/form/fieldStyles'
import SelectControl from '@/components/atoms/form/SelectControl'
import {
  categoryOptions,
  subtypeLabels,
  subtypesByCategory,
} from '@/components/features/trainings/trainingLabels'
import { newRequirement, type WeekFormInput } from '@/components/features/weeks/weekFormValues'

interface RequirementsFieldProps {
  control: Control<WeekFormInput>
  register: UseFormRegister<WeekFormInput>
  setValue: UseFormSetValue<WeekFormInput>
}

/** Editor for a week's session requirements: a list of (category, subtype, count)
 *  rows. The subtype options depend on the row's chosen category. */
function RequirementsField({ control, register, setValue }: RequirementsFieldProps) {
  const { fields, append, remove } = useFieldArray({ control, name: 'requirements' })
  // Watch all rows so each subtype select reflects its category live.
  const rows = useWatch({ control, name: 'requirements' })

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-lg font-semibold text-slate-100">Sesiones recomendadas</h3>

      {fields.length === 0 && (
        <p className="text-sm text-slate-500">Todavía no hay sesiones recomendadas.</p>
      )}

      <ul className="flex flex-col gap-2">
        {fields.map((field, index) => {
          const category = rows?.[index]?.category
          const subtypeOptions = category ? (subtypesByCategory[category] ?? []) : []
          return (
            <li
              key={field.id}
              className="flex flex-wrap items-end gap-3 rounded-md border border-slate-700 bg-slate-900/50 p-3"
            >
              <label className="flex flex-1 flex-col gap-1 text-xs font-medium text-slate-400">
                Categoría
                <SelectControl
                  {...register(`requirements.${index}.category`, {
                    // Changing category invalidates any chosen subtype.
                    onChange: () => setValue(`requirements.${index}.subtype`, ''),
                  })}
                  aria-label="Categoría"
                  className={`${controlClass} w-full py-1.5 text-sm`}
                  options={[{ value: '', label: 'Selecciona…' }, ...categoryOptions]}
                />
              </label>

              <label className="flex flex-1 flex-col gap-1 text-xs font-medium text-slate-400">
                Subtipo
                <SelectControl
                  {...register(`requirements.${index}.subtype`)}
                  disabled={!category}
                  aria-label="Subtipo"
                  className={`${controlClass} w-full py-1.5 text-sm`}
                  options={[
                    { value: '', label: category ? 'Selecciona…' : 'Elige categoría' },
                    ...subtypeOptions.map((subtype) => ({
                      value: subtype,
                      label: subtypeLabels[subtype],
                    })),
                  ]}
                />
              </label>

              <label className="flex w-20 flex-col gap-1 text-xs font-medium text-slate-400">
                Sesiones
                <input
                  {...register(`requirements.${index}.count`)}
                  inputMode="numeric"
                  aria-label="Sesiones"
                  className={`${controlClass} w-full py-1.5 text-sm`}
                />
              </label>

              <button
                type="button"
                onClick={() => remove(index)}
                aria-label="Eliminar sesión recomendada"
                className="mb-0.5 rounded p-1.5 text-slate-400 transition-colors hover:bg-red-500/15 hover:text-red-300 focus:ring-2 focus:ring-red-400 focus:outline-none"
              >
                <Trash2 size={16} />
              </button>
            </li>
          )
        })}
      </ul>

      <button
        type="button"
        onClick={() => append(newRequirement())}
        className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-4 py-2 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      >
        <Plus size={16} />
        Añadir sesión
      </button>

      {/* The label is referenced once so a screen reader announces the group. */}
      <span className={`sr-only ${labelClass}`}>Sesiones recomendadas por tipo</span>
    </div>
  )
}

export default RequirementsField
