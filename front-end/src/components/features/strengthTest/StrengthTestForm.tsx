import { zodResolver } from '@hookform/resolvers/zod'
import { Plus } from 'lucide-react'
import { useFieldArray, useForm } from 'react-hook-form'

import FormError from '@/components/atoms/form/FormError'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import StrengthTestItemRow from '@/components/features/strengthTest/StrengthTestItemRow'
import {
  newItem,
  type StrengthTestFormInput,
  strengthTestFormSchema,
  type StrengthTestFormValues,
} from '@/components/features/strengthTest/strengthTestFormValues'

interface StrengthTestFormProps {
  /** Collects the data; the parent owns the async PUT. */
  onSubmit: (values: StrengthTestFormValues) => Promise<void>
  defaultValues?: StrengthTestFormInput
  rootError?: string | undefined
}

function StrengthTestForm({ onSubmit, defaultValues, rootError }: StrengthTestFormProps) {
  const {
    register,
    control,
    setValue,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<StrengthTestFormInput, unknown, StrengthTestFormValues>({
    resolver: zodResolver(strengthTestFormSchema),
    defaultValues: defaultValues ?? { items: [] },
  })
  const { fields, append, remove } = useFieldArray({ control, name: 'items' })

  return (
    <form
      onSubmit={(event) => void handleSubmit(onSubmit)(event)}
      noValidate
      className="flex flex-col gap-6"
    >
      <div className="flex flex-col gap-3">
        <h3 className="text-lg font-semibold text-slate-100">Ejercicios de la prueba</h3>

        {fields.length === 0 && (
          <p className="text-sm text-slate-500">Todavía no hay ejercicios en la prueba.</p>
        )}

        <ul className="flex flex-col gap-2">
          {fields.map((field, index) => (
            <StrengthTestItemRow
              key={field.id}
              index={index}
              control={control}
              register={register}
              setValue={setValue}
              onRemove={() => remove(index)}
            />
          ))}
        </ul>

        {errors.items?.message && <p className="text-sm text-red-400">{errors.items.message}</p>}

        <button
          type="button"
          onClick={() => append(newItem())}
          className="inline-flex items-center gap-2 self-start rounded-md border border-dashed border-slate-600 px-4 py-2 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <Plus size={16} />
          Añadir ejercicio
        </button>
      </div>

      <div className="flex max-w-md flex-col gap-4">
        <FormError message={rootError} />
        <SubmitButton pending={isSubmitting} pendingLabel="Guardando…">
          Guardar cambios
        </SubmitButton>
      </div>
    </form>
  )
}

export default StrengthTestForm
