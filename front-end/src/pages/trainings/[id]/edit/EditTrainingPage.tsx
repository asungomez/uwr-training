import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import TrainingForm, { type TrainingFormValues } from '@/components/features/trainings/TrainingForm'
import {
  categoryLabels,
  categorySlugs,
  exerciseTypeForCategory,
  subtypeLabels,
  subtypeSlugs,
} from '@/components/features/trainings/trainingLabels'
import {
  formValuesToBlocks,
  trainingToFormValues,
} from '@/components/features/trainings/trainingFormValues'
import { useToast } from '@/components/toast/context'

function EditTrainingPage() {
  const { id } = useParams<{ id: string }>()
  const trainingId = id ?? ''
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  const { data, isLoading, error } = useQuery('/trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })

  async function handleSubmit(values: TrainingFormValues) {
    setRootError(undefined)
    // Category and subtype are immutable, so the body only carries title + blocks.
    const { error: putError } = await api.PUT('/trainings/{training_id}', {
      params: { path: { training_id: trainingId } },
      body: {
        title: values.title || null,
        blocks: formValuesToBlocks(values),
      },
    })
    if (putError) {
      setRootError(errorMessage(putError))
      return
    }
    toast.success('Entrenamiento actualizado.')
    await mutate(['/trainings'])
    await mutate(['/trainings/{training_id}', { params: { path: { training_id: trainingId } } }])
    void navigate(`/entrenamientos/${trainingId}`)
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        {data && (
          <>
            <Link
              to={`/entrenamientos/${categorySlugs[data.category]}`}
              className="transition-colors hover:text-slate-200"
            >
              {categoryLabels[data.category]}
            </Link>
            <ChevronRight size={14} />
            <Link
              to={`/entrenamientos/${categorySlugs[data.category]}/${subtypeSlugs[data.subtype]}`}
              className="transition-colors hover:text-slate-200"
            >
              {subtypeLabels[data.subtype]}
            </Link>
            <ChevronRight size={14} />
            <Link
              to={`/entrenamientos/${trainingId}`}
              className="transition-colors hover:text-slate-200"
            >
              {data.title ?? 'Sin título'}
            </Link>
            <ChevronRight size={14} />
          </>
        )}
        <span className="text-slate-200">Editar</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el entrenamiento.</p>}

      {data && (
        <>
          <h2 className="mt-6 text-2xl font-semibold tracking-tight">
            Editar entrenamiento · {categoryLabels[data.category]} / {subtypeLabels[data.subtype]}
          </h2>
          <div className="mt-6">
            <TrainingForm
              onSubmit={handleSubmit}
              exerciseType={exerciseTypeForCategory[data.category]}
              defaultValues={trainingToFormValues(data)}
              rootError={rootError}
              submitLabel="Guardar cambios"
              pendingLabel="Guardando…"
            />
          </div>
        </>
      )}
    </section>
  )
}

export default EditTrainingPage
