import { Check, Repeat2, X } from 'lucide-react'
import { useState } from 'react'

import type { components } from '@/api/schema'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import ExerciseLogList from '@/components/features/exercises/ExerciseLogList'
import { prescriptionFields } from '@/components/features/trainings/prescription'

type ItemResponse = components['schemas']['ItemResponse']
type LogFormExercise = components['schemas']['LogFormExercise']

export type EntryAction = 'pending' | 'done' | 'skipped'

export interface SeriesEntryState {
  action: EntryAction
  /** The performed exercise id — the prescribed one or a chosen alternative. */
  performedExerciseId: string
  paramValues: Record<string, string>
}

interface SeriesLogCardProps {
  /** The prescribed series item (for the exercise name + prescription line). */
  item: ItemResponse
  /** The log-form info for this exercise (alternatives + parameters), if any. */
  formExercise: LogFormExercise | undefined
  state: SeriesEntryState
  onChange: (state: SeriesEntryState) => void
  /** Open the exercise's full description in the side panel. */
  onSelectExercise: (exerciseId: string) => void
}

/** One series item in the "start session" flow: read the prescription, open the
 *  full description, switch to an alternative, mark done/skipped, and (when done)
 *  record the exercise's parameters. */
function SeriesLogCard({
  item,
  formExercise,
  state,
  onChange,
  onSelectExercise,
}: SeriesLogCardProps) {
  const [picking, setPicking] = useState(false)
  const fields = prescriptionFields(item)
  const alternatives = formExercise?.alternatives ?? []
  const plannedId = item.exercise_id ?? ''
  const isAlternative = state.performedExerciseId !== plannedId

  // The chosen alternative (when swapped) drives the name and which parameters to
  // record — each exercise has its own parameters.
  const performedAlt = alternatives.find((alt) => alt.exercise_id === state.performedExerciseId)
  const performedName = isAlternative
    ? (performedAlt?.name ?? item.exercise_name)
    : item.exercise_name
  const parameters = isAlternative
    ? (performedAlt?.parameters ?? [])
    : (formExercise?.parameters ?? [])

  function performWith(exerciseId: string) {
    onChange({ ...state, performedExerciseId: exerciseId })
    setPicking(false)
  }

  function onSwitchClick() {
    // One alternative → switch directly; several → open a picker to choose.
    const only = alternatives.length === 1 ? alternatives[0] : undefined
    if (only) {
      performWith(only.exercise_id)
    } else {
      setPicking((value) => !value)
    }
  }

  return (
    <li
      className={`rounded-lg border bg-slate-800/50 p-4 transition-colors ${
        state.action === 'done'
          ? 'border-emerald-600/50'
          : state.action === 'skipped'
            ? 'border-slate-700 opacity-60'
            : 'border-slate-700'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <button
            type="button"
            onClick={() => onSelectExercise(state.performedExerciseId || plannedId)}
            className="text-left font-medium text-indigo-400 transition-colors hover:text-indigo-300"
          >
            {performedName}
          </button>
          {isAlternative && (
            <span className="ml-2 text-xs text-amber-300">
              (alternativa de {item.exercise_name})
            </span>
          )}
          {fields.length > 0 && (
            <span className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm text-slate-400">
              {fields.map((field) => (
                <span key={field.label}>
                  {field.label}: <span className="text-slate-200">{field.value}</span>
                </span>
              ))}
            </span>
          )}
          {item.text && <p className="mt-1 text-sm text-slate-400">{item.text}</p>}
        </div>

        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={() =>
              onChange({ ...state, action: state.action === 'done' ? 'pending' : 'done' })
            }
            aria-pressed={state.action === 'done'}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus:ring-2 focus:ring-indigo-400 focus:outline-none ${
              state.action === 'done'
                ? 'bg-emerald-600 text-white hover:bg-emerald-500'
                : 'border border-slate-600 text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Check size={14} />
            Hecho
          </button>
          <button
            type="button"
            onClick={() =>
              onChange({ ...state, action: state.action === 'skipped' ? 'pending' : 'skipped' })
            }
            aria-pressed={state.action === 'skipped'}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus:ring-2 focus:ring-indigo-400 focus:outline-none ${
              state.action === 'skipped'
                ? 'bg-slate-600 text-white hover:bg-slate-500'
                : 'border border-slate-600 text-slate-200 hover:bg-slate-800'
            }`}
          >
            <X size={14} />
            No hecho
          </button>
        </div>
      </div>

      {alternatives.length > 0 && (
        <div className="mt-3">
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={onSwitchClick}
              className="inline-flex items-center gap-1.5 text-sm text-slate-300 transition-colors hover:text-white"
            >
              <Repeat2 size={14} />
              Cambiar a ejercicio alternativo
            </button>
            {isAlternative && (
              <button
                type="button"
                onClick={() => performWith(plannedId)}
                className="text-sm text-slate-400 transition-colors hover:text-slate-200"
              >
                Volver al estándar ({item.exercise_name})
              </button>
            )}
          </div>

          {picking && (
            <ul className="mt-2 flex flex-col gap-1 rounded-md border border-slate-700 bg-slate-900 p-1">
              {alternatives.map((alt) => (
                <li key={alt.exercise_id}>
                  <button
                    type="button"
                    onClick={() => performWith(alt.exercise_id)}
                    className={`w-full rounded px-3 py-2 text-left text-sm transition-colors hover:bg-slate-700 ${
                      alt.exercise_id === state.performedExerciseId
                        ? 'text-indigo-300'
                        : 'text-slate-200'
                    }`}
                  >
                    {alt.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {state.action === 'done' && parameters.length > 0 && (
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {parameters.map((param) => (
            <label
              key={param.parameter_id}
              className="flex flex-col gap-1 text-xs font-medium text-slate-400"
            >
              {param.name}
              <input
                value={state.paramValues[param.parameter_id] ?? ''}
                onChange={(event) =>
                  onChange({
                    ...state,
                    paramValues: {
                      ...state.paramValues,
                      [param.parameter_id]: event.target.value,
                    },
                  })
                }
                aria-label={`${param.name} (${item.exercise_name})`}
                className={`${controlClass} w-full py-1.5 text-sm`}
              />
            </label>
          ))}
        </div>
      )}

      {/* History for the exercise actually being performed (standard or chosen
          alternative) — a reference for the parameters used last time. */}
      <div className="mt-4 border-t border-slate-700 pt-3">
        <ExerciseLogList exerciseId={state.performedExerciseId || plannedId} compact />
      </div>
    </li>
  )
}

export default SeriesLogCard
