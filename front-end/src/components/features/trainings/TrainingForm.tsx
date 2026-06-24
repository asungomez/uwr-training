import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import FormError from '@/components/atoms/form/FormError'
import SelectField from '@/components/atoms/form/SelectField'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'
import {
  categoryOptions,
  subtypeLabels,
  subtypesByCategory,
} from '@/components/features/trainings/trainingLabels'

type Category = (typeof categoryOptions)[number]['value']

// Empty string is each <select>'s "unselected" state; refine to require a real one.
const schema = z.object({
  title: z.string().trim(),
  category: z
    .enum(['', 'gym', 'pool', 'cardio'])
    .refine((value): value is Category => value !== '', { message: 'La categoría es obligatoria' }),
  subtype: z.string().min(1, 'El subtipo es obligatorio'),
})

export type TrainingFormValues = z.infer<typeof schema>

interface TrainingFormProps {
  /** Collects the data; the parent owns the async call (create or update). */
  onSubmit: (values: TrainingFormValues) => Promise<void>
  defaultValues?: Partial<z.input<typeof schema>>
  /** Form-level error from the parent (e.g. an API failure). */
  rootError?: string | undefined
  /** Submit button labels — defaults suit creation; override for editing. */
  submitLabel?: string
  pendingLabel?: string
}

function TrainingForm({
  onSubmit,
  defaultValues,
  rootError,
  submitLabel = 'Crear entrenamiento',
  pendingLabel = 'Creando…',
}: TrainingFormProps) {
  const {
    register,
    control,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<z.input<typeof schema>, unknown, TrainingFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: '', category: '', subtype: '', ...defaultValues },
  })

  // useWatch (not watch()) so React Compiler can memoize this component.
  const category = useWatch({ control, name: 'category' })
  const subtypeOptions = (category ? (subtypesByCategory[category] ?? []) : []).map((value) => ({
    value,
    label: subtypeLabels[value],
  }))

  return (
    <form
      onSubmit={(event) => void handleSubmit(onSubmit)(event)}
      noValidate
      className="flex max-w-md flex-col gap-4"
    >
      <TextField
        id="training-title"
        label="Título"
        error={errors.title?.message}
        {...register('title')}
      />
      <SelectField
        id="training-category"
        label="Categoría"
        error={errors.category?.message}
        options={[{ value: '', label: 'Selecciona una categoría' }, ...categoryOptions]}
        {...register('category', {
          // Changing category clears any chosen subtype (it may no longer be valid).
          onChange: () => setValue('subtype', ''),
        })}
      />
      <SelectField
        id="training-subtype"
        label="Subtipo"
        error={errors.subtype?.message}
        disabled={!category}
        options={[
          { value: '', label: category ? 'Selecciona un subtipo' : 'Elige una categoría primero' },
          ...subtypeOptions,
        ]}
        {...register('subtype')}
      />

      <FormError message={rootError} />

      <SubmitButton pending={isSubmitting} pendingLabel={pendingLabel}>
        {submitLabel}
      </SubmitButton>
    </form>
  )
}

export default TrainingForm
