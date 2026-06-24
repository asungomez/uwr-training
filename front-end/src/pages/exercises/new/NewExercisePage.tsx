import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, useMutate } from '@/api/client'
import { errorMessage } from '@/api/errors'
import ExerciseForm, { type ExerciseFormValues } from '@/components/features/exercises/ExerciseForm'
import { useToast } from '@/components/toast/context'

function NewExercisePage() {
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  async function handleSubmit(values: ExerciseFormValues) {
    setRootError(undefined)
    const { data, error } = await api.POST('/exercises', {
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
    if (error || !data) {
      setRootError(errorMessage(error))
      return
    }
    toast.success('Ejercicio creado.')
    await mutate(['/exercises'])
    void navigate(`/ejercicios/${data.id}`)
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/ejercicios" className="transition-colors hover:text-slate-200">
          Ejercicios
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Nuevo ejercicio</span>
      </nav>

      <h2 className="mt-6 text-2xl font-semibold tracking-tight">Nuevo ejercicio</h2>

      <div className="mt-6">
        <ExerciseForm onSubmit={handleSubmit} rootError={rootError} />
      </div>
    </section>
  )
}

export default NewExercisePage
