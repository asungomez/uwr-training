import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import WeekForm from '@/components/features/weeks/WeekForm'
import {
  formValuesToRequirements,
  weekToFormValues,
  type WeekFormValues,
} from '@/components/features/weeks/weekFormValues'
import { useToast } from '@/components/toast/context'

function EditWeekPage() {
  const { id } = useParams<{ id: string }>()
  const weekId = id ?? ''
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  const { data, isLoading, error } = useQuery('/weeks/{week_id}', {
    params: { path: { week_id: weekId } },
  })

  async function handleSubmit(values: WeekFormValues) {
    setRootError(undefined)
    const { error: putError } = await api.PUT('/weeks/{week_id}', {
      params: { path: { week_id: weekId } },
      body: {
        name: values.name,
        recommended_date: values.recommendedDate || null,
        phase: values.phase,
        requirements: formValuesToRequirements(values),
      },
    })
    if (putError) {
      setRootError(errorMessage(putError))
      return
    }
    toast.success('Semana actualizada.')
    await mutate(['/weeks'])
    await mutate(['/weeks/{week_id}', { params: { path: { week_id: weekId } } }])
    void navigate(`/calendario/${weekId}`)
  }

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/calendario" className="transition-colors hover:text-slate-200">
          Calendario
        </Link>
        <ChevronRight size={14} />
        {data && (
          <>
            <Link to={`/calendario/${weekId}`} className="transition-colors hover:text-slate-200">
              {data.name}
            </Link>
            <ChevronRight size={14} />
          </>
        )}
        <span className="text-slate-200">Editar</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado la semana.</p>}

      {data && (
        <>
          <h2 className="mt-6 text-2xl font-semibold tracking-tight">Editar semana</h2>
          <div className="mt-6">
            <WeekForm
              onSubmit={handleSubmit}
              defaultValues={weekToFormValues(data)}
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

export default EditWeekPage
