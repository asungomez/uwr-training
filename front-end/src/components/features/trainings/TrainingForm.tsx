import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import FormError from '@/components/atoms/form/FormError'
import SelectField from '@/components/atoms/form/SelectField'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'

const categoryOptions = [
  { value: 'gym', label: 'Gimnasio' },
  { value: 'pool', label: 'Piscina' },
  { value: 'cardio', label: 'Cardio' },
] as const

type Category = (typeof categoryOptions)[number]['value']

// Subtype options per category, mirroring SUBTYPES_BY_CATEGORY on the back-end.
const subtypesByCategory: Record<Category, { value: string; label: string }[]> = {
  gym: [
    { value: 'adaptation', label: 'Adaptación' },
    { value: 'accumulation', label: 'Acumulación' },
    { value: 'transmutation', label: 'Transmutación' },
    { value: 'realization', label: 'Realización' },
  ],
  pool: [
    { value: 'endurance', label: 'Resistencia' },
    { value: 'anaerobic', label: 'Anaeróbico' },
    { value: 'alactic', label: 'Aláctico' },
  ],
  cardio: [
    { value: 'aerobic', label: 'Aeróbico' },
    { value: 'anaerobic', label: 'Anaeróbico' },
  ],
}

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
}

function TrainingForm({ onSubmit, defaultValues, rootError }: TrainingFormProps) {
  const {
    register,
    control,
    handleSubmit,
    resetField,
    formState: { errors, isSubmitting },
  } = useForm<z.input<typeof schema>, unknown, TrainingFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: '', category: '', subtype: '', ...defaultValues },
  })

  // useWatch (not watch()) so React Compiler can memoize this component.
  const category = useWatch({ control, name: 'category' })
  const subtypeOptions = category ? (subtypesByCategory[category] ?? []) : []

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
          // Changing category invalidates any chosen subtype.
          onChange: () => resetField('subtype'),
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

      <SubmitButton pending={isSubmitting} pendingLabel="Creando…">
        Crear entrenamiento
      </SubmitButton>
    </form>
  )
}

export default TrainingForm
