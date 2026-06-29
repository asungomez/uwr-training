import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import ExerciseForm, { type ExerciseFormValues } from '@/components/features/exercises/ExerciseForm'
import { useToast } from '@/components/toast/context'

function EditExercisePage() {
  const { id } = useParams<{ id: string }>()
  const exerciseId = id ?? ''
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  const { data, isLoading, error } = useQuery('/exercises/{exercise_id}', {
    params: { path: { exercise_id: exerciseId } },
  })

  async function handleSubmit(values: ExerciseFormValues) {
    setRootError(undefined)
    const { error: putError } = await api.PUT('/exercises/{exercise_id}', {
      params: { path: { exercise_id: exerciseId } },
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
    if (putError) {
      setRootError(errorMessage(putError))
      return
    }
    toast.success('Ejercicio actualizado.')
    await mutate(['/exercises'])
    await mutate(['/exercises/{exercise_id}', { params: { path: { exercise_id: exerciseId } } }])
    void navigate(`/ejercicios/${exerciseId}`)
  }

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/ejercicios" className="transition-colors hover:text-slate-200">
          Ejercicios
        </Link>
        <ChevronRight size={14} />
        {data && (
          <>
            <Link
              to={`/ejercicios/${exerciseId}`}
              className="transition-colors hover:text-slate-200"
            >
              {data.name}
            </Link>
            <ChevronRight size={14} />
          </>
        )}
        <span className="text-slate-200">Editar</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el ejercicio.</p>}

      {data && (
        <>
          <h2 className="mt-6 text-2xl font-semibold tracking-tight">Editar ejercicio</h2>
          <div className="mt-6">
            <ExerciseForm
              onSubmit={handleSubmit}
              defaultValues={{
                name: data.name,
                description: data.description ?? '',
                type: data.type,
                thumbnailKey: data.thumbnail_key ?? null,
                videoKey: data.video_key ?? null,
                relatedExercises: data.related_exercises.map((related) => ({
                  exerciseId: related.related_exercise_id,
                  exerciseName: related.related_exercise_name,
                  note: related.note ?? '',
                })),
                parameters: data.parameters.map((param) => ({
                  name: param.name,
                  description: param.description ?? '',
                })),
              }}
              initialThumbnailUrl={data.thumbnail_url}
              initialVideoUrl={data.video_url}
              excludeExerciseId={data.id}
              rootError={rootError}
            />
          </div>
        </>
      )}
    </section>
  )
}

export default EditExercisePage
