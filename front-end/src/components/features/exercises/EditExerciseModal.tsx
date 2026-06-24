import { useState } from 'react'

import { api, useMutate } from '@/api/client'
import { errorMessage } from '@/api/errors'
import type { components } from '@/api/schema'
import Modal from '@/components/atoms/Modal'
import { useToast } from '@/components/toast/context'

import ExerciseForm, { type ExerciseFormValues } from './ExerciseForm'

type Exercise = components['schemas']['ExerciseResponse']

interface EditExerciseModalProps {
  /** The exercise being edited, or null when the modal is closed. */
  exercise: Exercise | null
  onClose: () => void
}

function EditExerciseModal({ exercise, onClose }: EditExerciseModalProps) {
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  function handleClose() {
    setRootError(undefined)
    onClose()
  }

  async function handleSubmit(values: ExerciseFormValues) {
    if (!exercise) return
    setRootError(undefined)
    const { error } = await api.PUT('/exercises/{exercise_id}', {
      params: { path: { exercise_id: exercise.id } },
      body: {
        name: values.name,
        description: values.description || null,
        type: values.type,
        thumbnail_key: values.thumbnailKey,
        video_key: values.videoKey,
        related_exercises: values.relatedExercises.map((related) => ({
          related_exercise_id: related.exerciseId,
          note: related.note || null,
        })),
        parameters: values.parameters.map((param) => ({
          name: param.name,
          description: param.description || null,
        })),
      },
    })
    if (error) {
      setRootError(errorMessage(error))
      return
    }
    toast.success('Ejercicio actualizado.')
    // Revalidate both the list and this exercise's detail view.
    await mutate(['/exercises'])
    await mutate(['/exercises/{exercise_id}', { params: { path: { exercise_id: exercise.id } } }])
    handleClose()
  }

  return (
    <Modal
      open={exercise !== null}
      onClose={handleClose}
      title="Editar ejercicio"
      size="xl"
      closeOnBackdrop={false}
    >
      {exercise && (
        <ExerciseForm
          // Re-mount per exercise so the form re-seeds its default values.
          key={exercise.id}
          onSubmit={handleSubmit}
          defaultValues={{
            name: exercise.name,
            description: exercise.description ?? '',
            type: exercise.type,
            thumbnailKey: exercise.thumbnail_key ?? null,
            videoKey: exercise.video_key ?? null,
            relatedExercises: exercise.related_exercises.map((related) => ({
              exerciseId: related.related_exercise_id,
              exerciseName: related.related_exercise_name,
              note: related.note ?? '',
            })),
            parameters: exercise.parameters.map((param) => ({
              name: param.name,
              description: param.description ?? '',
            })),
          }}
          initialThumbnailUrl={exercise.thumbnail_url}
          initialVideoUrl={exercise.video_url}
          excludeExerciseId={exercise.id}
          rootError={rootError}
        />
      )}
    </Modal>
  )
}

export default EditExerciseModal
