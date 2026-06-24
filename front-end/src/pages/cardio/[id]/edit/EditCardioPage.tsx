import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import {
  type CardioFormValues,
  cardioToFormValues,
  formValuesToItems,
} from '@/components/features/cardio/cardioFormValues'
import CardioForm from '@/components/features/cardio/CardioForm'
import { cardioSubtypeLabels, cardioSubtypeSlugs } from '@/components/features/cardio/cardioLabels'
import { useToast } from '@/components/toast/context'

function EditCardioPage() {
  const { id } = useParams<{ id: string }>()
  const trainingId = id ?? ''
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  const { data, isLoading, error } = useQuery('/cardio-trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })

  async function handleSubmit(values: CardioFormValues) {
    setRootError(undefined)
    // Subtype is immutable, so the body only carries title + items.
    const { error: putError } = await api.PUT('/cardio-trainings/{training_id}', {
      params: { path: { training_id: trainingId } },
      body: {
        title: values.title || null,
        items: formValuesToItems(values),
      },
    })
    if (putError) {
      setRootError(errorMessage(putError))
      return
    }
    toast.success('Entrenamiento actualizado.')
    await mutate(['/cardio-trainings'])
    await mutate([
      '/cardio-trainings/{training_id}',
      { params: { path: { training_id: trainingId } } },
    ])
    void navigate(`/entrenamientos/cardio/sesion/${trainingId}`)
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <Link to="/entrenamientos/cardio" className="transition-colors hover:text-slate-200">
          Cardio
        </Link>
        {data && (
          <>
            <ChevronRight size={14} />
            <Link
              to={`/entrenamientos/cardio/${cardioSubtypeSlugs[data.subtype]}`}
              className="transition-colors hover:text-slate-200"
            >
              {cardioSubtypeLabels[data.subtype]}
            </Link>
            <ChevronRight size={14} />
            <Link
              to={`/entrenamientos/cardio/sesion/${trainingId}`}
              className="transition-colors hover:text-slate-200"
            >
              {data.title ?? 'Sin título'}
            </Link>
          </>
        )}
        <ChevronRight size={14} />
        <span className="text-slate-200">Editar</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el entrenamiento.</p>}

      {data && (
        <>
          <h2 className="mt-6 text-2xl font-semibold tracking-tight">
            Editar entrenamiento · Cardio / {cardioSubtypeLabels[data.subtype]}
          </h2>
          <div className="mt-6">
            <CardioForm
              onSubmit={handleSubmit}
              defaultValues={cardioToFormValues(data)}
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

export default EditCardioPage
