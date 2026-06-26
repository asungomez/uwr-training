import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import type { components } from '@/api/schema'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import FormError from '@/components/atoms/form/FormError'
import SelectControl from '@/components/atoms/form/SelectControl'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import ExercisePanel from '@/components/features/trainings/ExercisePanel'
import { useToast } from '@/components/toast/context'

import SeriesLogCard, { type SeriesEntryState } from './SeriesLogCard'

type ItemResponse = components['schemas']['ItemResponse']

function RegisterSessionPage() {
  const { id } = useParams<{ id: string }>()
  const trainingId = id ?? ''
  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)
  const [submitting, setSubmitting] = useState(false)
  const [note, setNote] = useState('')
  const [weekId, setWeekId] = useState('')
  // The exercise shown in the description side panel (local — no URL param here).
  const [panelExerciseId, setPanelExerciseId] = useState<string | null>(null)

  // The full session structure (blocks/items + prescription) and the log-form
  // (per-exercise alternatives + parameters). Merged by exercise id.
  const training = useQuery('/trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })
  const form = useQuery('/trainings/{training_id}/log-form', {
    params: { path: { training_id: trainingId } },
  })

  const isLoading = training.isLoading || form.isLoading
  const error = training.error ?? form.error
  const data = training.data
  const formByExerciseId = new Map(
    (form.data?.exercises ?? []).map((exercise) => [exercise.exercise_id, exercise]),
  )

  // Per-item athlete state, keyed by item id (the same exercise in two items is
  // tracked independently). Initialized once the session loads.
  const [entries, setEntries] = useState<Record<string, SeriesEntryState>>({})
  const [syncedData, setSyncedData] = useState(data)
  if (data !== syncedData) {
    setSyncedData(data)
    if (data) {
      const initial: Record<string, SeriesEntryState> = {}
      for (const block of data.blocks) {
        for (const sub of block.sub_blocks) {
          for (const item of sub.items) {
            if (item.kind === 'series' && item.exercise_id) {
              initial[item.id] = {
                action: 'pending',
                performedExerciseId: item.exercise_id,
                paramValues: {},
              }
            }
          }
        }
      }
      setEntries(initial)
    }
  }

  // Pre-select the recommended week once the form loads (resynced if it changes);
  // tracked separately so a manual choice isn't clobbered on re-render.
  const [syncedForm, setSyncedForm] = useState(form.data)
  if (form.data !== syncedForm) {
    setSyncedForm(form.data)
    setWeekId(form.data?.recommended_week_id ?? '')
  }

  function setEntry(itemId: string, state: SeriesEntryState) {
    setEntries((prev) => ({ ...prev, [itemId]: state }))
  }

  // All series items in order (for building the submission).
  const seriesItems: ItemResponse[] = (data?.blocks ?? [])
    .flatMap((block) => block.sub_blocks)
    .flatMap((sub) => sub.items)
    .filter((item) => item.kind === 'series' && item.exercise_id)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setRootError(undefined)

    const body = {
      note: note.trim() || null,
      week_id: weekId || null,
      entries: seriesItems.map((item) => {
        const plannedId = item.exercise_id ?? ''
        const state = entries[item.id]
        if (state?.action !== 'done') {
          return {
            planned_exercise_id: plannedId,
            action: 'skipped' as const,
            parameter_values: [],
          }
        }
        const formExercise = formByExerciseId.get(plannedId)
        return {
          planned_exercise_id: plannedId,
          action: 'done' as const,
          performed_exercise_id: state.performedExerciseId || plannedId,
          parameter_values: (formExercise?.parameters ?? [])
            .map((param) => ({
              parameter_id: param.parameter_id,
              value: state.paramValues[param.parameter_id] ?? '',
            }))
            .filter((value) => value.value.trim() !== ''),
        }
      }),
    }

    const { error: postError } = await api.POST('/trainings/{training_id}/logs', {
      params: { path: { training_id: trainingId } },
      body,
    })
    setSubmitting(false)
    if (postError) {
      setRootError(errorMessage(postError))
      return
    }
    toast.success('Sesión registrada.')
    void navigate(`/entrenamientos/${trainingId}`)
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <Link
          to={`/entrenamientos/${trainingId}`}
          className="transition-colors hover:text-slate-200"
        >
          {data?.title ?? '…'}
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registrar</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el entrenamiento.</p>}

      {data && (
        <div
          className={
            panelExerciseId
              ? 'lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(0,28rem)] lg:items-start lg:gap-8'
              : ''
          }
        >
          <div className="min-w-0">
            <h1 className="mt-6 text-2xl font-semibold tracking-tight text-slate-100">
              Registrar sesión
            </h1>
            <p className="mt-1 text-slate-400">{data.title ?? 'Sin título'}</p>

            {seriesItems.length === 0 ? (
              <p className="mt-6 text-sm text-slate-500">
                Este entrenamiento no tiene ejercicios que registrar.
              </p>
            ) : (
              <form
                onSubmit={(event) => void handleSubmit(event)}
                noValidate
                className="mt-6 flex flex-col gap-8"
              >
                {data.blocks.map((block) => (
                  <div key={block.id}>
                    <h2 className="text-xl font-semibold text-slate-100">{block.name}</h2>
                    {block.sub_blocks.map((sub) => (
                      <div key={sub.id} className="mt-4">
                        <h3 className="font-medium text-slate-200">{sub.name}</h3>
                        {sub.notes && <p className="mt-1 text-sm text-slate-400">{sub.notes}</p>}
                        <ul className="mt-3 flex flex-col gap-3">
                          {sub.items.map((item) =>
                            item.kind === 'note' ? (
                              <li key={item.id} className="text-sm text-slate-400">
                                {item.text}
                              </li>
                            ) : (
                              <SeriesLogCard
                                key={item.id}
                                item={item}
                                formExercise={
                                  item.exercise_id
                                    ? formByExerciseId.get(item.exercise_id)
                                    : undefined
                                }
                                state={
                                  entries[item.id] ?? {
                                    action: 'pending',
                                    performedExerciseId: item.exercise_id ?? '',
                                    paramValues: {},
                                  }
                                }
                                onChange={(state) => setEntry(item.id, state)}
                                onSelectExercise={setPanelExerciseId}
                              />
                            ),
                          )}
                        </ul>
                      </div>
                    ))}
                  </div>
                ))}

                <div className="flex flex-col gap-4 border-t border-slate-800 pt-6">
                  {(form.data?.weeks.length ?? 0) > 0 && (
                    <label className="flex max-w-sm flex-col gap-1 text-sm font-medium text-slate-300">
                      Semana (opcional)
                      <SelectControl
                        value={weekId}
                        onChange={(event) => setWeekId(event.target.value)}
                        aria-label="Semana"
                        className={`${controlClass} mt-1 w-full text-sm`}
                        options={[
                          { value: '', label: 'Sin semana' },
                          ...(form.data?.weeks ?? []).map((week) => ({
                            value: week.id,
                            label: week.name,
                          })),
                        ]}
                      />
                    </label>
                  )}

                  <label className="flex flex-col gap-1 text-sm font-medium text-slate-300">
                    Nota de la sesión (opcional)
                    <textarea
                      value={note}
                      onChange={(event) => setNote(event.target.value)}
                      rows={3}
                      placeholder="Algo que recordar para la próxima vez…"
                      className={`${controlClass} mt-1 w-full text-sm`}
                    />
                  </label>
                  <FormError message={rootError} />
                  <SubmitButton pending={submitting} pendingLabel="Guardando…">
                    Finalizar sesión
                  </SubmitButton>
                </div>
              </form>
            )}
          </div>

          {panelExerciseId && (
            <ExercisePanel
              exerciseId={panelExerciseId}
              onClose={() => setPanelExerciseId(null)}
              onSelectExercise={setPanelExerciseId}
            />
          )}
        </div>
      )}
    </section>
  )
}

export default RegisterSessionPage
