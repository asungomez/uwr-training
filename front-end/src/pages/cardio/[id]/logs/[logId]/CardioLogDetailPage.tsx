import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import SelectControl from '@/components/atoms/form/SelectControl'
import { formatLogDate } from '@/components/features/trainings/logFormat'
import { useToast } from '@/components/toast/context'

function CardioLogDetailPage() {
  const { id, logId } = useParams<{ id: string; logId: string }>()
  const trainingId = id ?? ''
  const toast = useToast()
  const mutate = useMutate()
  const [savingWeek, setSavingWeek] = useState(false)

  const { data, isLoading, error } = useQuery('/cardio-trainings/{training_id}/logs/{log_id}', {
    params: { path: { training_id: trainingId, log_id: logId ?? '' } },
  })
  // The weeks this session can be assigned to (those recommending its type).
  const form = useQuery('/cardio-trainings/{training_id}/log-form', {
    params: { path: { training_id: trainingId } },
  })

  async function changeWeek(weekId: string) {
    setSavingWeek(true)
    const { error: patchError } = await api.PATCH(
      '/cardio-trainings/{training_id}/logs/{log_id}/week',
      {
        params: { path: { training_id: trainingId, log_id: logId ?? '' } },
        body: { week_id: weekId || null },
      },
    )
    setSavingWeek(false)
    if (patchError) {
      toast.error(errorMessage(patchError))
      return
    }
    await mutate([
      '/cardio-trainings/{training_id}/logs/{log_id}',
      { params: { path: { training_id: trainingId, log_id: logId ?? '' } } },
    ])
    toast.success('Semana actualizada.')
  }

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <Link to="/entrenamientos/cardio" className="transition-colors hover:text-slate-200">
          Cardio
        </Link>
        <ChevronRight size={14} />
        <Link
          to={`/entrenamientos/cardio/sesion/${trainingId}`}
          className="transition-colors hover:text-slate-200"
        >
          {form.data?.title ?? '…'}
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registro</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el registro.</p>}

      {data && (
        <div className="mt-6 max-w-2xl">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
            {formatLogDate(data.performed_at)}
          </h1>
          {data.exercise && <p className="mt-2 text-slate-200">{data.exercise}</p>}
          {data.note && <p className="mt-2 text-slate-300">{data.note}</p>}

          {(() => {
            // Selectable weeks = those still open for this type, plus the log's
            // current week (which may now be full but must stay selectable here).
            const options = (form.data?.weeks ?? []).map((week) => ({
              value: week.id,
              label: week.name,
            }))
            if (data.week_id && !options.some((o) => o.value === data.week_id)) {
              options.unshift({ value: data.week_id, label: data.week_name ?? 'Semana' })
            }
            if (options.length === 0) return null
            return (
              <label className="mt-4 flex max-w-sm flex-col gap-1 text-sm font-medium text-slate-300">
                Semana
                <SelectControl
                  value={data.week_id ?? ''}
                  onChange={(event) => void changeWeek(event.target.value)}
                  disabled={savingWeek}
                  aria-label="Semana"
                  className={`${controlClass} mt-1 w-full text-sm`}
                  options={[{ value: '', label: 'Sin semana' }, ...options]}
                />
              </label>
            )
          })()}
        </div>
      )}
    </section>
  )
}

export default CardioLogDetailPage
