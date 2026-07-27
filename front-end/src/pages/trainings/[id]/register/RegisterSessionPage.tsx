import { Check, ChevronRight, Hourglass, Loader2, RotateCcw, TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
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
type TrainingDetail = components['schemas']['TrainingSessionDetailResponse']
type SessionLog = components['schemas']['SessionLogResponse']
interface NamedItem {
  id: string
  name: string
}

// Collapse rapid edits (e.g. typing a weight) into a single auto-save PUT.
const SAVE_DEBOUNCE_MS = 800
// How long the "Guardado" confirmation lingers before fading back to idle.
const SAVED_VISIBLE_MS = 2000
// Interval between retries after a failed save (one global loop, latest snapshot).
const SAVE_RETRY_MS = 5000

// Auto-save lifecycle shown by the indicator: nothing pending, in-flight, done, failed.
type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

const SAVE_CONFIG = {
  saving: {
    icon: <Loader2 size={13} className="animate-spin" />,
    label: 'Guardando',
    cls: 'border-slate-600 bg-slate-800 text-slate-300',
  },
  saved: {
    icon: <Check size={13} />,
    label: 'Guardado',
    cls: 'border-emerald-600/50 bg-slate-800 text-emerald-300',
  },
  error: {
    icon: <TriangleAlert size={13} />,
    label: 'Error al guardar',
    cls: 'border-red-600/50 bg-slate-800 text-red-300',
  },
} as const

/** A small, unintrusive auto-save indicator, fixed to the bottom of the viewport so
 *  it stays visible while scrolling a long session on a phone. Fades in when there's
 *  something to show and fades out when the status returns to idle. */
function SaveIndicator({ status }: { status: SaveStatus }) {
  // Keep the last non-idle config mounted through the fade-out (idle → opacity 0 →
  // unmount, on transition end), so the pill doesn't vanish abruptly when "Guardado"
  // clears. Updated during render (not an effect) per the set-state-in-render pattern.
  const [shown, setShown] = useState<Exclude<SaveStatus, 'idle'> | null>(null)
  if (status !== 'idle' && status !== shown) setShown(status)
  const visible = status !== 'idle'
  if (!shown) return null

  const config = SAVE_CONFIG[shown]
  return (
    <div
      role="status"
      aria-live="polite"
      onTransitionEnd={() => {
        if (!visible) setShown(null)
      }}
      className={`fixed bottom-4 left-1/2 z-30 flex -translate-x-1/2 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium shadow-lg transition-opacity duration-500 ${config.cls} ${visible ? 'opacity-100' : 'opacity-0'}`}
    >
      {config.icon}
      {config.label}
    </div>
  )
}

/** The per-item form state to start from: every series item pending, unless an
 *  in-progress partial pre-fills it. A partial's entries reference the planned
 *  exercise (not the item), so they're matched to items by planned exercise in order
 *  — the same order both were built in — which lines up repeats of one exercise. */
function buildInitialEntries(
  data: TrainingDetail,
  partial: SessionLog | null,
): { entries: Record<string, SeriesEntryState>; hasPartial: boolean } {
  const items = data.blocks
    .flatMap((block) => block.sub_blocks)
    .flatMap((sub) => sub.items)
    .filter((item) => item.kind === 'series' && item.exercise_id)

  const entries: Record<string, SeriesEntryState> = {}
  for (const item of items) {
    entries[item.id] = {
      action: 'pending',
      performedExerciseId: item.exercise_id ?? '',
      paramValues: {},
    }
  }

  const partialEntries = partial?.entries ?? []
  if (partialEntries.length === 0) return { entries, hasPartial: false }

  // Remaining items per planned exercise id, consumed in order.
  const itemsByExercise = new Map<string, string[]>()
  for (const item of items) {
    const key = item.exercise_id ?? ''
    if (!itemsByExercise.has(key)) itemsByExercise.set(key, [])
    itemsByExercise.get(key)!.push(item.id)
  }

  let matched = false
  for (const entry of partialEntries) {
    const plannedId = entry.planned_exercise_id
    if (!plannedId) continue
    const queue = itemsByExercise.get(plannedId)
    const itemId = queue?.shift()
    if (!itemId) continue
    matched = true
    const paramValues: Record<string, string> = {}
    for (const value of entry.parameter_values) paramValues[value.parameter_id] = value.value
    entries[itemId] = {
      action: entry.action,
      performedExerciseId: entry.performed_exercise_id ?? plannedId,
      paramValues,
    }
  }
  return { entries, hasPartial: matched }
}

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
  // Auto-save state, surfaced by a small fixed indicator so the athlete (on a phone,
  // mid-workout) can trust their progress is being saved.
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  // --- Auto-save machinery (see runSave/scheduleSave/scheduleRetry below) ---
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  // The latest form snapshot, read at save time so a retry always sends current state
  // (not the state that failed). Updated in lockstep with `entries`.
  const latestEntriesRef = useRef<Record<string, SeriesEntryState>>({})
  // The in-flight PUT (or null): lets us serialize a clear/submit behind it, and avoid
  // overlapping saves.
  const inFlightRef = useRef<Promise<void> | null>(null)
  // A save requested while one was in flight — re-run once it settles.
  const dirtyRef = useRef(false)
  // Set by clear/submit: no new save may start, and any in-flight/queued save must not
  // touch status or reschedule a retry (its write would resurrect a just-removed draft).
  const savesSuspendedRef = useRef(false)

  // "Guardado" is a fleeting confirmation — fade it back to idle after a moment.
  // "Guardando" and "Error al guardar" persist (an error shouldn't vanish on its own).
  useEffect(() => {
    if (saveStatus !== 'saved') return
    const id = setTimeout(() => setSaveStatus('idle'), SAVED_VISIBLE_MS)
    return () => clearTimeout(id)
  }, [saveStatus])

  // On unmount, stop the debounce + retry timers so they don't fire on a gone page.
  useEffect(() => {
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current)
      if (retryTimer.current) clearTimeout(retryTimer.current)
    }
  }, [])

  // The full session structure (blocks/items + prescription) and the log-form
  // (per-exercise alternatives + parameters). Merged by exercise id.
  const training = useQuery('/trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })
  const form = useQuery('/trainings/{training_id}/log-form', {
    params: { path: { training_id: trainingId } },
  })
  // The athlete's latest strength-test result per exercise, to turn a series' load %
  // into an absolute kg (same as the training detail view). Keyed by exercise id.
  const { data: latestResults } = useQuery('/strength-test-logs/latest-results', {})
  const testWeightByExercise = new Map(
    (latestResults?.results ?? []).map((result) => [result.exercise_id, result.weight_kg]),
  )

  const isLoading = training.isLoading || form.isLoading
  const error = training.error ?? form.error
  const data = training.data
  const formByExerciseId = new Map(
    (form.data?.exercises ?? []).map((exercise) => [exercise.exercise_id, exercise]),
  )

  // Per-item athlete state, keyed by item id (the same exercise in two items is
  // tracked independently). Initialized once both the session and the log-form (which
  // carries any in-progress partial) have loaded.
  const [entries, setEntries] = useState<Record<string, SeriesEntryState>>({})
  // Whether we resumed an in-progress draft — drives the "continuing" banner.
  const [resumed, setResumed] = useState(false)
  // Init once both queries resolve; re-run only if the log-form reference changes.
  const [initedForm, setInitedForm] = useState<typeof form.data>(undefined)
  if (data && form.data && form.data !== initedForm) {
    setInitedForm(form.data)
    const { entries: initial, hasPartial } = buildInitialEntries(data, form.data.partial ?? null)
    setEntries(initial)
    setResumed(hasPartial)
  }

  // Mirror the latest committed entries into a ref, so a retry (which fires later, off
  // a timer) always reads the current snapshot rather than the state that failed. Ref
  // writes belong in an effect, not render.
  useEffect(() => {
    latestEntriesRef.current = entries
  }, [entries])

  // Pre-select the recommended week once the form loads (resynced if it changes);
  // tracked separately so a manual choice isn't clobbered on re-render.
  const [syncedForm, setSyncedForm] = useState(form.data)
  if (form.data !== syncedForm) {
    setSyncedForm(form.data)
    setWeekId(form.data?.recommended_week_id ?? '')
  }

  // The submission payload for one series item, from its current state. Shared by the
  // full submit and the partial (auto-saved) log seed.
  function entryPayload(item: ItemResponse, state: SeriesEntryState | undefined) {
    const plannedId = item.exercise_id ?? ''
    if (state?.action !== 'done') {
      return { planned_exercise_id: plannedId, action: 'skipped' as const, parameter_values: [] }
    }
    const formExercise = formByExerciseId.get(plannedId)
    const performedId = state.performedExerciseId || plannedId
    // Parameters belong to the exercise actually performed — the planned one, or the
    // chosen alternative (which carries its own parameters).
    const performedParams =
      performedId === plannedId
        ? (formExercise?.parameters ?? [])
        : (formExercise?.alternatives.find((alt) => alt.exercise_id === performedId)?.parameters ??
          [])
    return {
      planned_exercise_id: plannedId,
      action: 'done' as const,
      performed_exercise_id: performedId,
      parameter_values: performedParams
        .map((param) => ({
          parameter_id: param.parameter_id,
          value: state.paramValues[param.parameter_id] ?? '',
        }))
        .filter((value) => value.value.trim() !== ''),
    }
  }

  // Auto-save the partial log on every change, so progress survives a phone lock +
  // page reload. Only touched items (done/skipped, or with a recorded value) are sent —
  // pending ones are omitted so they don't come back as "skipped". The PUT upserts the
  // draft. See runSave for the debounce / retry / single-flight machinery.
  function touchedEntries(source: Record<string, SeriesEntryState>): ItemResponse[] {
    return seriesItems.filter((item) => {
      const state = source[item.id]
      return (
        state != null &&
        (state.action !== 'pending' ||
          Object.values(state.paramValues).some((value) => value.trim() !== ''))
      )
    })
  }

  function clearRetry() {
    if (retryTimer.current) {
      clearTimeout(retryTimer.current)
      retryTimer.current = null
    }
  }

  // One global retry loop: after a failed save, retry the LATEST snapshot on an interval
  // until it succeeds (or a clear/submit suspends saving). If a retry is already pending
  // we leave it — edits don't spawn their own cycles; the single timer picks up the
  // latest state when it fires.
  function scheduleRetry() {
    if (retryTimer.current || savesSuspendedRef.current) return
    retryTimer.current = setTimeout(() => {
      retryTimer.current = null
      void runSave()
    }, SAVE_RETRY_MS)
  }

  // Persist the latest snapshot. Single-flight: if a PUT is already in flight, mark dirty
  // and let it re-run on settle, so we never fire overlapping PUTs and the last write
  // wins. Failure starts/continues the retry loop; success stops it.
  async function runSave(): Promise<void> {
    if (savesSuspendedRef.current) return
    if (inFlightRef.current) {
      dirtyRef.current = true
      return
    }
    const touched = touchedEntries(latestEntriesRef.current)
    // Nothing meaningful yet → don't create an empty draft.
    if (touched.length === 0) return
    setSaveStatus('saving')
    const promise = api
      .PUT('/trainings/{training_id}/logs/partial', {
        params: { path: { training_id: trainingId } },
        body: {
          entries: touched.map((item) => entryPayload(item, latestEntriesRef.current[item.id])),
        },
      })
      .then(({ error: putError }) => {
        if (savesSuspendedRef.current) return
        if (putError) {
          setSaveStatus('error')
          scheduleRetry()
        } else {
          setSaveStatus('saved')
          clearRetry()
        }
      })
      .catch(() => {
        if (savesSuspendedRef.current) return
        setSaveStatus('error')
        scheduleRetry()
      })
    inFlightRef.current = promise
    await promise
    inFlightRef.current = null
    // Coalesced edits during the flight → save again with the newest snapshot.
    if (!savesSuspendedRef.current && dirtyRef.current) {
      dirtyRef.current = false
      void runSave()
    }
  }

  // Debounced entry point: collapse rapid edits (e.g. typing a weight) into one PUT.
  function scheduleSave() {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => {
      saveTimer.current = null
      void runSave()
    }, SAVE_DEBOUNCE_MS)
  }

  function setEntry(itemId: string, state: SeriesEntryState) {
    setEntries((prev) => ({ ...prev, [itemId]: state }))
    // The effect syncing `latestEntriesRef` commits before this debounced save fires.
    scheduleSave()
  }

  // All series items in order (for building the submission).
  const seriesItems: ItemResponse[] = (data?.blocks ?? [])
    .flatMap((block) => block.sub_blocks)
    .flatMap((sub) => sub.items)
    .filter((item) => item.kind === 'series' && item.exercise_id)

  // The union of materials/facilities to bring: across every series item's
  // currently-performed exercise (the prescribed one, or the alternative the athlete
  // switched to — so the lists update live with each swap). Deduped by id, kept in
  // first-seen order. `pick` selects which list (gym_materials / gym_facilities).
  function neededAcrossExercises(
    pick: (source: { gym_materials: NamedItem[]; gym_facilities: NamedItem[] }) => NamedItem[],
  ): NamedItem[] {
    const byId = new Map<string, string>()
    for (const item of seriesItems) {
      const plannedId = item.exercise_id ?? ''
      const formExercise = formByExerciseId.get(plannedId)
      if (!formExercise) continue
      const performedId = entries[item.id]?.performedExerciseId ?? plannedId
      const performed =
        performedId === plannedId
          ? formExercise
          : formExercise.alternatives.find((alt) => alt.exercise_id === performedId)
      if (!performed) continue
      for (const entry of pick(performed)) {
        if (!byId.has(entry.id)) byId.set(entry.id, entry.name)
      }
    }
    return [...byId.entries()].map(([itemId, name]) => ({ id: itemId, name }))
  }

  const materials = neededAcrossExercises((source) => source.gym_materials)
  const facilities = neededAcrossExercises((source) => source.gym_facilities)

  // Stop all auto-saving/retrying and wait for any in-flight PUT to finish, so a
  // subsequent submit/clear (POST/DELETE) is guaranteed to be the last write — no late
  // PUT can resurrect a draft the server just superseded or removed. Idempotent.
  async function suspendSaves() {
    savesSuspendedRef.current = true
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = null
    clearRetry()
    dirtyRef.current = false
    if (inFlightRef.current) await inFlightRef.current
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    // Submitting supersedes the draft server-side; make sure no auto-save races it.
    await suspendSaves()
    setSubmitting(true)
    setRootError(undefined)

    const body = {
      note: note.trim() || null,
      week_id: weekId || null,
      entries: seriesItems.map((item) => entryPayload(item, entries[item.id])),
    }

    const { error: postError } = await api.POST('/trainings/{training_id}/logs', {
      params: { path: { training_id: trainingId } },
      body,
    })
    setSubmitting(false)
    if (postError) {
      // Let the athlete edit + auto-save again if the submit itself failed.
      savesSuspendedRef.current = false
      setRootError(errorMessage(postError))
      return
    }
    toast.success('Sesión registrada.')
    void navigate(`/entrenamientos/${trainingId}`)
  }

  // "Start over": discard the in-progress draft and reset the form to pending.
  const [clearing, setClearing] = useState(false)
  async function handleClearPartial() {
    // Suspend saves (and drain any in-flight one) so nothing recreates the draft after
    // we delete it.
    await suspendSaves()
    setClearing(true)
    const { error: deleteError } = await api.DELETE('/trainings/{training_id}/logs/partial', {
      params: { path: { training_id: trainingId } },
    })
    setClearing(false)
    if (deleteError) {
      // Deletion failed — resume saving so the athlete isn't stuck.
      savesSuspendedRef.current = false
      toast.error(errorMessage(deleteError))
      return
    }
    if (data) setEntries(buildInitialEntries(data, null).entries)
    setNote('')
    setResumed(false)
    setSaveStatus('idle')
    // A fresh draft may be created again from the next edit.
    savesSuspendedRef.current = false
    toast.success('Progreso descartado.')
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

            {/* Non-invasive banner when we've resumed an auto-saved draft, with a way
                to discard it and start fresh. */}
            {resumed && (
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3">
                <p className="flex items-center gap-2 text-sm text-amber-200">
                  <Hourglass size={15} className="shrink-0" />
                  Seguimos donde lo dejaste. Tu progreso se guardó automáticamente.
                </p>
                <button
                  type="button"
                  onClick={() => void handleClearPartial()}
                  disabled={clearing}
                  className="inline-flex items-center gap-1.5 rounded-md border border-amber-500/50 px-3 py-1.5 text-sm font-medium text-amber-100 transition-colors hover:bg-amber-500/20 focus:ring-2 focus:ring-amber-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <RotateCcw size={14} />
                  Empezar de nuevo
                </button>
              </div>
            )}

            {materials.length > 0 && (
              <div className="mt-6 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
                <h2 className="text-sm font-medium tracking-wide text-slate-400 uppercase">
                  Materiales
                </h2>
                <ul className="mt-3 flex flex-wrap gap-2">
                  {materials.map((material) => (
                    <li
                      key={material.id}
                      className="inline-flex rounded-full border border-slate-600 bg-slate-800 px-3 py-1 text-sm text-slate-100"
                    >
                      {material.name}
                    </li>
                  ))}
                </ul>
                <p className="mt-3 text-xs text-slate-500">
                  La lista de materiales se actualiza si haces alguno de los ejercicios
                  alternativos.
                </p>
              </div>
            )}

            {facilities.length > 0 && (
              <div className="mt-4 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
                <h2 className="text-sm font-medium tracking-wide text-slate-400 uppercase">
                  Instalaciones
                </h2>
                <ul className="mt-3 flex flex-wrap gap-2">
                  {facilities.map((facility) => (
                    <li
                      key={facility.id}
                      className="inline-flex rounded-full border border-slate-600 bg-slate-800 px-3 py-1 text-sm text-slate-100"
                    >
                      {facility.name}
                    </li>
                  ))}
                </ul>
                <p className="mt-3 text-xs text-slate-500">
                  La lista de instalaciones se actualiza si haces alguno de los ejercicios
                  alternativos.
                </p>
              </div>
            )}

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
                                latestTestWeight={
                                  item.exercise_id
                                    ? (testWeightByExercise.get(item.exercise_id) ?? null)
                                    : null
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

          <SaveIndicator status={saveStatus} />
        </div>
      )}
    </section>
  )
}

export default RegisterSessionPage
