import { Plus, X } from 'lucide-react'
import {
  type Control,
  type FieldErrors,
  type UseFormRegister,
  useFieldArray,
} from 'react-hook-form'

import { controlClass, errorClass, labelClass } from '@/components/atoms/form/fieldStyles'

import type { ExerciseFormValues } from './ExerciseForm'

interface ExerciseParametersFieldProps {
  control: Control<ExerciseFormValues>
  register: UseFormRegister<ExerciseFormValues>
  errors: FieldErrors<ExerciseFormValues>
}

/** Manages an exercise's trackable parameters (e.g. "Peso", "Tiempo") — just
 *  their definitions: a required name and an optional description each. */
function ExerciseParametersField({ control, register, errors }: ExerciseParametersFieldProps) {
  const { fields, append, remove } = useFieldArray({ control, name: 'parameters' })

  return (
    <div className="flex flex-col gap-2">
      <span className={labelClass}>Parámetros</span>

      {fields.length > 0 && (
        <ul className="flex flex-col gap-2">
          {fields.map((field, index) => (
            <li
              key={field.id}
              className="flex flex-col gap-2 rounded-md border border-slate-700 bg-slate-900/50 p-3"
            >
              <div className="flex items-start gap-2">
                <div className="flex flex-1 flex-col gap-1">
                  <input
                    {...register(`parameters.${index}.name`)}
                    placeholder="Nombre (p. ej. Peso)"
                    className={`${controlClass} w-full text-sm`}
                  />
                  {errors.parameters?.[index]?.name && (
                    <p className={errorClass}>{errors.parameters[index]?.name?.message}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => remove(index)}
                  aria-label="Quitar parámetro"
                  className="mt-1 rounded p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                >
                  <X size={16} />
                </button>
              </div>
              <textarea
                {...register(`parameters.${index}.description`)}
                rows={2}
                placeholder="Descripción (opcional)…"
                className={`${controlClass} w-full text-sm`}
              />
            </li>
          ))}
        </ul>
      )}

      <button
        type="button"
        onClick={() => append({ name: '', description: '' })}
        className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-3 py-2 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      >
        <Plus size={16} />
        Añadir parámetro
      </button>
    </div>
  )
}

export default ExerciseParametersField
