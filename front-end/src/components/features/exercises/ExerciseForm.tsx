import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'

import FormError from '@/components/atoms/form/FormError'
import MarkdownField from '@/components/atoms/form/MarkdownField'
import MediaUploadField from '@/components/atoms/form/MediaUploadField'
import SelectField from '@/components/atoms/form/SelectField'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'

const schema = z.object({
  name: z.string().trim().min(1, 'El nombre es obligatorio'),
  description: z.string().trim(),
  type: z.enum(['gym', 'pool']),
  thumbnailKey: z.string().nullable(),
  videoKey: z.string().nullable(),
})

export type ExerciseFormValues = z.infer<typeof schema>

interface ExerciseFormProps {
  /** Collects the data; the parent owns the async call (create or update). */
  onSubmit: (values: ExerciseFormValues) => Promise<void>
  defaultValues?: Partial<ExerciseFormValues>
  /** Preview URLs for media already saved on the exercise (edit mode). */
  initialThumbnailUrl?: string | null | undefined
  initialVideoUrl?: string | null | undefined
  /** Form-level error from the parent (e.g. an API failure). */
  rootError?: string | undefined
}

function ExerciseForm({
  onSubmit,
  defaultValues,
  initialThumbnailUrl,
  initialVideoUrl,
  rootError,
}: ExerciseFormProps) {
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ExerciseFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: 'gym',
      description: '',
      name: '',
      thumbnailKey: null,
      videoKey: null,
      ...defaultValues,
    },
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
      <Controller
        control={control}
        name="description"
        render={({ field }) => (
          <MarkdownField
            label="Descripción"
            value={field.value}
            onChange={field.onChange}
            error={errors.description?.message}
          />
        )}
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
      <Controller
        control={control}
        name="thumbnailKey"
        render={({ field }) => (
          <MediaUploadField
            label="Miniatura"
            kind="thumbnail"
            value={field.value}
            onChange={field.onChange}
            initialPreviewUrl={initialThumbnailUrl}
          />
        )}
      />
      <Controller
        control={control}
        name="videoKey"
        render={({ field }) => (
          <MediaUploadField
            label="Vídeo"
            kind="video"
            value={field.value}
            onChange={field.onChange}
            initialPreviewUrl={initialVideoUrl}
          />
        )}
      />

      <FormError message={rootError} />

      <SubmitButton pending={isSubmitting} pendingLabel="Guardando…">
        Guardar ejercicio
      </SubmitButton>
    </form>
  )
}

export default ExerciseForm
