import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import type { z } from 'zod'

import {
  cardioFormSchema,
  type CardioFormValues,
} from '@/components/features/cardio/cardioFormValues'
import CardioItemsEditor from '@/components/features/cardio/blocks/CardioItemsEditor'
import FormError from '@/components/atoms/form/FormError'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'

interface CardioFormProps {
  /** Collects the data; the parent owns the async call (create or update). */
  onSubmit: (values: CardioFormValues) => Promise<void>
  defaultValues?: Partial<z.input<typeof cardioFormSchema>>
  /** Form-level error from the parent (e.g. an API failure). */
  rootError?: string | undefined
  submitLabel?: string
  pendingLabel?: string
}

function CardioForm({
  onSubmit,
  defaultValues,
  rootError,
  submitLabel = 'Crear entrenamiento',
  pendingLabel = 'Creando…',
}: CardioFormProps) {
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.input<typeof cardioFormSchema>, unknown, CardioFormValues>({
    resolver: zodResolver(cardioFormSchema),
    defaultValues: { title: '', items: [], ...defaultValues },
  })

  return (
    <form
      onSubmit={(event) => void handleSubmit(onSubmit)(event)}
      noValidate
      className="flex flex-col gap-8"
    >
      <div className="flex max-w-md flex-col gap-4">
        <TextField
          id="cardio-title"
          label="Título"
          error={errors.title?.message}
          {...register('title')}
        />
      </div>

      <div className="border-t border-slate-800 pt-8">
        <Controller
          control={control}
          name="items"
          render={({ field }) => (
            <CardioItemsEditor value={field.value} onChange={field.onChange} />
          )}
        />
      </div>

      <div className="flex max-w-md flex-col gap-4">
        <FormError message={rootError} />
        <SubmitButton pending={isSubmitting} pendingLabel={pendingLabel}>
          {submitLabel}
        </SubmitButton>
      </div>
    </form>
  )
}

export default CardioForm
