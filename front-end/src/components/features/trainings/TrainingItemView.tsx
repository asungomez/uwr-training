import { Info, TriangleAlert } from 'lucide-react'

import type { components } from '@/api/schema'
import Tooltip from '@/components/molecules/Tooltip'

import { prescriptionFields } from './prescription'
import { evaluateTargetTime, formatTargetTime } from './targetTime'

type ItemResponse = components['schemas']['ItemResponse']

interface TrainingItemViewProps {
  item: ItemResponse
  /** Open the series' exercise in the side panel (by id). */
  onSelectExercise: (exerciseId: string) => void
  /** The athlete's latest strength-test result (kg) for this item's exercise, used
   *  to turn the load % into an absolute load. `null`/`undefined` = no result yet,
   *  so the load shows as a bare % with a warning. */
  latestTestWeight?: number | null
  /** The athlete's latest lactic-test personal best (seconds), used to compute a pool
   *  item's target time from its formula. `null`/`undefined` = no result yet, so the
   *  target shows as the bare formula with a warning. */
  personalBest?: number | null
}

/** Render one sub-block item on the detail page: a note as plain text, a series
 *  as its exercise name (clickable, opens the exercise panel) plus only the
 *  prescription fields that were filled in. */
function TrainingItemView({
  item,
  onSelectExercise,
  latestTestWeight,
  personalBest,
}: TrainingItemViewProps) {
  if (item.kind === 'note') {
    return <li className="text-slate-300">{item.text}</li>
  }

  const fields = prescriptionFields(item)
  // A load is shown only when the admin set a percentage on this item. With a test
  // result, show the absolute kg; otherwise show the % with a warning.
  const hasLoad = item.load_percentage != null
  const loadKg =
    hasLoad && latestTestWeight != null
      ? Math.round((item.load_percentage! / 100) * latestTestWeight)
      : null
  // A target time is shown when the admin set a formula (pool items). With a personal
  // best, compute the absolute seconds; otherwise show the formula with a warning.
  const targetSeconds =
    item.target_time_formula != null && personalBest != null
      ? evaluateTargetTime(item.target_time_formula, personalBest)
      : null

  return (
    <li className="break-words text-slate-300">
      {item.exercise_id ? (
        <button
          type="button"
          onClick={() => onSelectExercise(item.exercise_id!)}
          className="text-left font-medium break-words text-indigo-400 transition-colors hover:text-indigo-300"
        >
          {item.exercise_name}
        </button>
      ) : (
        <span className="font-medium text-slate-100">{item.exercise_name}</span>
      )}
      {fields.length > 0 && (
        <span className="ml-2 inline-flex flex-wrap gap-x-3 gap-y-1 text-slate-400">
          {fields.map((field) => (
            <span key={field.label}>
              {field.label}: <span className="text-slate-200">{field.value}</span>
            </span>
          ))}
        </span>
      )}
      {hasLoad && (
        <span className="ml-2 inline-flex items-center gap-1 text-slate-400">
          Carga:{' '}
          {loadKg != null ? (
            <Tooltip label="Calculada a partir del resultado de tu última prueba">
              <span className="inline-flex items-center gap-1 text-slate-200">
                {loadKg} kg <span className="text-slate-500">({item.load_percentage}%)</span>
                <Info size={14} className="text-slate-500" />
              </span>
            </Tooltip>
          ) : (
            <Tooltip label="Haz una prueba de fuerza para calcular una carga más precisa">
              <span className="inline-flex items-center gap-1 text-amber-300">
                {item.load_percentage}%
                <TriangleAlert size={14} />
              </span>
            </Tooltip>
          )}
        </span>
      )}
      {item.target_time_formula != null && (
        <span className="ml-2 inline-flex items-center gap-1 text-slate-400">
          Tiempo objetivo:{' '}
          {targetSeconds != null ? (
            <Tooltip
              label={`Calculado a partir de tu última marca personal (${formatTargetTime(personalBest!)})`}
            >
              <span className="inline-flex items-center gap-1 text-slate-200">
                {formatTargetTime(targetSeconds)}{' '}
                <span className="text-slate-500">({item.target_time_formula})</span>
                <Info size={14} className="text-slate-500" />
              </span>
            </Tooltip>
          ) : (
            <Tooltip label="Haz una prueba de ácido láctico para calcular el tiempo objetivo">
              <span className="inline-flex items-center gap-1 text-amber-300">
                {item.target_time_formula}
                <TriangleAlert size={14} />
              </span>
            </Tooltip>
          )}
        </span>
      )}
      {item.text && <p className="mt-0.5 text-slate-400">{item.text}</p>}
    </li>
  )
}

export default TrainingItemView
