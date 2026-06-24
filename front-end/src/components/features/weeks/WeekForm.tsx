import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import type { z } from 'zod'

import FormError from '@/components/atoms/form/FormError'
import SelectField from '@/components/atoms/form/SelectField'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'
import RequirementsField from '@/components/features/weeks/RequirementsField'
import { phaseOptions } from '@/components/features/weeks/weekLabels'
import { weekFormSchema, type WeekFormValues } from '@/components/features/weeks/weekFormValues'

interface WeekFormProps {
  /** Collects the data; the parent owns the async call (create or update). */
  onSubmit: (values: WeekFormValues) => Promise<void>
  defaultValues?: Partial<z.input<typeof weekFormSchema>>
  rootError?: string | undefined
  submitLabel?: string
  pendingLabel?: string
}

function WeekForm({
  onSubmit,
  defaultValues,
  rootError,
  submitLabel = 'Crear semana',
  pendingLabel = 'Creando…',
}: WeekFormProps) {
  const {
    register,
    control,
    setValue,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.input<typeof weekFormSchema>, unknown, WeekFormValues>({
    resolver: zodResolver(weekFormSchema),
    defaultValues: {
      name: '',
      recommendedDate: '',
      phase: 'adaptation',
      requirements: [],
      ...defaultValues,
    },
  })

  return (
    <form
      onSubmit={(event) => void handleSubmit(onSubmit)(event)}
      noValidate
      className="flex flex-col gap-8"
    >
      <div className="flex max-w-md flex-col gap-4">
        <TextField
          id="week-name"
          label="Nombre"
          error={errors.name?.message}
          {...register('name')}
        />
        <TextField
          id="week-date"
          label="Fecha recomendada"
          placeholder="p. ej. Semana del 3 de marzo"
          error={errors.recommendedDate?.message}
          {...register('recommendedDate')}
        />
        <SelectField
          id="week-phase"
          label="Fase del mesociclo"
          options={phaseOptions}
          error={errors.phase?.message}
          {...register('phase')}
        />
      </div>

      <div className="border-t border-slate-800 pt-8">
        <RequirementsField control={control} register={register} setValue={setValue} />
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

export default WeekForm
