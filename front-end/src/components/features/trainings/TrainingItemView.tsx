import type { components } from '@/api/schema'

import { prescriptionFields } from './prescription'

type ItemResponse = components['schemas']['ItemResponse']

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

  const fields = prescriptionFields(item)
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
      {item.text && <p className="mt-0.5 text-slate-400">{item.text}</p>}
    </li>
  )
}

export default TrainingItemView
