import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import FormError from '@/components/atoms/form/FormError'
import SelectField from '@/components/atoms/form/SelectField'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextAreaField from '@/components/atoms/form/TextAreaField'
import TextField from '@/components/atoms/form/TextField'

const schema = z.object({
  name: z.string().trim().min(1, 'El nombre es obligatorio'),
  description: z.string().trim(),
  type: z.enum(['gym', 'pool']),
})

export type ExerciseFormValues = z.infer<typeof schema>

interface ExerciseFormProps {
  /** Collects the data; the parent owns the async call (create or update). */
  onSubmit: (values: ExerciseFormValues) => Promise<void>
  defaultValues?: Partial<ExerciseFormValues>
  /** Form-level error from the parent (e.g. an API failure). */
  rootError?: string | undefined
}

function ExerciseForm({ onSubmit, defaultValues, rootError }: ExerciseFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ExerciseFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { type: 'gym', description: '', name: '', ...defaultValues },
  })

  return (
    <form
      onSubmit={(event) => void handleSubmit(onSubmit)(event)}
      noValidate
      className="flex flex-col gap-4"
    >
      <TextField
        id="exercise-name"
        label="Nombre"
        error={errors.name?.message}
        {...register('name')}
      />
      <TextAreaField
        id="exercise-description"
        label="Descripción"
        rows={3}
        error={errors.description?.message}
        {...register('description')}
      />
      <SelectField
        id="exercise-type"
        label="Tipo"
        error={errors.type?.message}
        options={[
          { value: 'gym', label: 'Gimnasio' },
          { value: 'pool', label: 'Piscina' },
        ]}
        {...register('type')}
      />

      <FormError message={rootError} />

      <SubmitButton pending={isSubmitting} pendingLabel="Guardando…">
        Guardar ejercicio
      </SubmitButton>
    </form>
  )
}

export default ExerciseForm
