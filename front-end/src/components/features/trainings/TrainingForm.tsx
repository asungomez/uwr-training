import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'

import type { components } from '@/api/schema'
import FormError from '@/components/atoms/form/FormError'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'
import TrainingBlocksEditor from '@/components/features/trainings/blocks/TrainingBlocksEditor'

type ExerciseType = components['schemas']['ExerciseType']

// Category and subtype now come from the URL (immutable), so the form only owns
// the title and the block tree.
const schema = z.object({
  title: z.string().trim(),
  // Client-side id (for list keys + DnD) plus the editable fields. Items are a
  // discriminated union: a free-text note or an exercise series (its numeric
  // fields are strings here — parsed at the API boundary).
  blocks: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      subBlocks: z.array(
        z.object({
          id: z.string(),
          name: z.string(),
          notes: z.string(),
          items: z.array(
            z.discriminatedUnion('kind', [
              z.object({ id: z.string(), kind: z.literal('note'), text: z.string() }),
              z.object({
                id: z.string(),
                kind: z.literal('series'),
                exerciseId: z.string().min(1, 'Selecciona un ejercicio'),
                exerciseName: z.string(),
                sets: z.string(),
                reps: z.string(),
                time: z.string(),
                distance: z.string(),
                effort: z.string(),
                load: z.string(),
                notes: z.string(),
              }),
            ]),
          ),
        }),
      ),
    }),
  ),
})

export type TrainingFormValues = z.infer<typeof schema>

interface TrainingFormProps {
  /** Collects the data; the parent owns the async call (create or update). */
  onSubmit: (values: TrainingFormValues) => Promise<void>
  /** Restrict the exercise picker to this type (null = no restriction, e.g. cardio). */
  exerciseType: ExerciseType | null
  defaultValues?: Partial<z.input<typeof schema>>
  /** Form-level error from the parent (e.g. an API failure). */
  rootError?: string | undefined
  /** Submit button labels — defaults suit creation; override for editing. */
  submitLabel?: string
  pendingLabel?: string
}

function TrainingForm({
  onSubmit,
  exerciseType,
  defaultValues,
  rootError,
  submitLabel = 'Crear entrenamiento',
  pendingLabel = 'Creando…',
}: TrainingFormProps) {
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.input<typeof schema>, unknown, TrainingFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: '', blocks: [], ...defaultValues },
  })

  return (
    <form
      onSubmit={(event) => void handleSubmit(onSubmit)(event)}
      noValidate
      className="flex flex-col gap-8"
    >
      <div className="flex max-w-md flex-col gap-4">
        <TextField
          id="training-title"
          label="Título"
          error={errors.title?.message}
          {...register('title')}
        />
      </div>

      <div className="border-t border-slate-800 pt-8">
        <Controller
          control={control}
          name="blocks"
          render={({ field }) => (
            <TrainingBlocksEditor
              value={field.value}
              onChange={field.onChange}
              exerciseType={exerciseType}
            />
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

export default TrainingForm
