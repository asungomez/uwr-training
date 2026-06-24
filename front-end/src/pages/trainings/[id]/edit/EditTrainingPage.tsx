import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import type { components } from '@/api/schema'
import TrainingForm, { type TrainingFormValues } from '@/components/features/trainings/TrainingForm'
import { trainingToFormValues } from '@/components/features/trainings/trainingFormValues'
import { useToast } from '@/components/toast/context'

type Subtype = components['schemas']['TrainingSubtype']

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
    const { error: putError } = await api.PUT('/trainings/{training_id}', {
      params: { path: { training_id: trainingId } },
      body: {
        category: values.category,
        subtype: values.subtype as Subtype,
        title: values.title || null,
        blocks: values.blocks.map((block) => ({
          name: block.name,
          sub_blocks: block.subBlocks.map((sub) => ({
            name: sub.name,
            notes: sub.notes || null,
            items: sub.items.map((item) => ({ kind: item.kind, text: item.text || null })),
          })),
        })),
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
          <h2 className="mt-6 text-2xl font-semibold tracking-tight">Editar entrenamiento</h2>
          <div className="mt-6">
            <TrainingForm
              onSubmit={handleSubmit}
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
