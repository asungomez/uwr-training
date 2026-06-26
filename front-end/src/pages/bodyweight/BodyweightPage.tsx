import { useState } from 'react'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import FormError from '@/components/atoms/form/FormError'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import BodyweightChart from '@/components/features/bodyweight/BodyweightChart'
import { formatLogDate } from '@/components/features/trainings/logFormat'
import Pagination from '@/components/molecules/Pagination'
import { useToast } from '@/components/toast/context'

const PAGE_SIZE = 10

function BodyweightPage() {
  const toast = useToast()
  const mutate = useMutate()
  const [weight, setWeight] = useState('')
  const [rootError, setRootError] = useState<string | undefined>(undefined)
  const [submitting, setSubmitting] = useState(false)
  const [page, setPage] = useState(1)

  // The paginated history (most recent first) and the recent-points graph data
  // are separate queries: navigating the list changes `page`, but the graph
  // (last 10, oldest first) stays put.
  const history = useQuery(
    '/bodyweight-logs',
    { params: { query: { page, page_size: PAGE_SIZE } } },
    { keepPreviousData: true },
  )
  const recent = useQuery('/bodyweight-logs/recent', {})

  const logs = history.data?.items ?? []
  const pageCount = Math.ceil((history.data?.total_count ?? 0) / PAGE_SIZE)
  const graphLogs = recent.data ?? []

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setRootError(undefined)
    const value = Number(weight.replace(',', '.'))
    if (!Number.isFinite(value) || value <= 0) {
      setRootError('Introduce un peso válido en kilos.')
      return
    }

    setSubmitting(true)
    const { error: postError } = await api.POST('/bodyweight-logs', {
      body: { weight_kg: value },
    })
    setSubmitting(false)
    if (postError) {
      setRootError(errorMessage(postError))
      return
    }
    setWeight('')
    // Refresh both the graph and the list; jump the list back to the first page
    // so the new measurement is visible at the top.
    setPage(1)
    await Promise.all([mutate(['/bodyweight-logs/recent']), mutate(['/bodyweight-logs'])])
    toast.success('Peso registrado.')
  }

  return (
    <section className="max-w-2xl">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Registro de peso</h1>
      <p className="mt-1 text-slate-400">Anota tu peso corporal y sigue su evolución.</p>

      <form
        onSubmit={(event) => void handleSubmit(event)}
        noValidate
        className="mt-6 flex flex-wrap items-end gap-3"
      >
        <label className="flex flex-col gap-1 text-sm font-medium text-slate-300">
          Peso actual (kg)
          <input
            type="number"
            inputMode="decimal"
            step="0.1"
            min="0"
            value={weight}
            onChange={(event) => setWeight(event.target.value)}
            placeholder="75,5"
            aria-label="Peso actual en kilos"
            className={`${controlClass} mt-1 w-40 text-sm`}
          />
        </label>
        <SubmitButton pending={submitting} pendingLabel="Guardando…">
          Guardar
        </SubmitButton>
      </form>
      <FormError message={rootError} />

      {graphLogs.length > 1 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-slate-100">Evolución reciente</h2>
          <div className="mt-3 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <BodyweightChart logs={graphLogs} />
          </div>
        </div>
      )}

      <div className="mt-10 border-t border-slate-800 pt-6">
        <h2 className="text-lg font-semibold text-slate-100">Historial</h2>

        {history.isLoading && <p className="mt-3 text-sm text-slate-400">Cargando…</p>}

        {history.data && logs.length === 0 && (
          <p className="mt-3 text-sm text-slate-500">Todavía no has registrado tu peso.</p>
        )}

        {logs.length > 0 && (
          <>
            <ul className="mt-3 flex flex-col gap-2">
              {logs.map((log) => (
                <li
                  key={log.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3"
                >
                  <span className="font-medium text-slate-100">{log.weight_kg} kg</span>
                  <span className="text-sm text-slate-400">{formatLogDate(log.recorded_at)}</span>
                </li>
              ))}
            </ul>
            <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
          </>
        )}
      </div>
    </section>
  )
}

export default BodyweightPage
