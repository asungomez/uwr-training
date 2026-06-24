import type { components } from '@/api/schema'

import { formatSecondsAsTime } from './seriesFormat'

type ItemResponse = components['schemas']['ItemResponse']

/** The series' populated prescription fields, in display order, as label/value
 *  pairs. Only fields the admin filled in are returned. */
function prescription(item: ItemResponse): { label: string; value: string }[] {
  const fields: { label: string; value: string }[] = []
  if (item.sets != null) fields.push({ label: 'Series', value: String(item.sets) })
  if (item.reps != null) fields.push({ label: 'Reps/serie', value: String(item.reps) })
  if (item.duration_seconds != null)
    fields.push({ label: 'Tiempo por serie', value: formatSecondsAsTime(item.duration_seconds) })
  if (item.distance_meters != null)
    fields.push({ label: 'Distancia', value: `${item.distance_meters} m` })
  if (item.effort) fields.push({ label: 'Intensidad', value: item.effort })
  return fields
}

interface TrainingItemViewProps {
  item: ItemResponse
  /** Open the series' exercise in the side panel (by id). */
  onSelectExercise: (exerciseId: string) => void
}

/** Render one sub-block item on the detail page: a note as plain text, a series
 *  as its exercise name (clickable, opens the exercise panel) plus only the
 *  prescription fields that were filled in. */
function TrainingItemView({ item, onSelectExercise }: TrainingItemViewProps) {
  if (item.kind === 'note') {
    return <li className="text-slate-300">{item.text}</li>
  }

  const fields = prescription(item)
  return (
    <li className="text-slate-300">
      {item.exercise_id ? (
        <button
          type="button"
          onClick={() => onSelectExercise(item.exercise_id!)}
          className="font-medium text-indigo-400 transition-colors hover:text-indigo-300"
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
      {item.text && <p className="mt-0.5 text-slate-400">{item.text}</p>}
    </li>
  )
}

export default TrainingItemView
