import { Link } from 'react-router-dom'

import type { components } from '@/api/schema'
import { ExerciseTypeBadge } from '@/components/features/exercises/exerciseBadges'
import Markdown from '@/components/molecules/Markdown'

type ExerciseResponse = components['schemas']['ExerciseResponse']

interface ExerciseDetailContentProps {
  exercise: ExerciseResponse
  /** When given, related-exercise clicks call this (panel mode) instead of
   *  navigating to the exercise's own page (default link mode). */
  onSelectExercise?: (exerciseId: string) => void
}

/** The body of an exercise (media, description, parameters, related), shared by
 *  the exercise detail page and the in-training exercise panel. The owner adds
 *  any surrounding chrome (breadcrumb, admin actions, close button). */
function ExerciseDetailContent({ exercise, onSelectExercise }: ExerciseDetailContentProps) {
  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-2xl font-semibold tracking-tight text-slate-100">{exercise.name}</h2>
        <ExerciseTypeBadge type={exercise.type} />
      </div>

      {exercise.video_url ? (
        <video
          src={exercise.video_url}
          poster={exercise.thumbnail_url ?? undefined}
          controls
          className="mt-4 w-full rounded-lg border border-slate-700"
        />
      ) : (
        exercise.thumbnail_url && (
          <img
            src={exercise.thumbnail_url}
            alt=""
            className="mt-4 w-full rounded-lg border border-slate-700 object-contain"
          />
        )
      )}

      {exercise.description ? (
        <Markdown className="mt-4 text-slate-300">{exercise.description}</Markdown>
      ) : (
        <p className="mt-4 text-slate-500">Sin descripción.</p>
      )}

      {exercise.parameters.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-slate-100">Parámetros</h3>
          <ul className="mt-3 flex flex-col gap-2">
            {exercise.parameters.map((param) => (
              <li key={param.id} className="rounded-lg border border-slate-700 bg-slate-800/50 p-3">
                <span className="font-medium text-slate-100">{param.name}</span>
                {param.description && (
                  <p className="mt-1 text-sm text-slate-300">{param.description}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {exercise.related_exercises.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-slate-100">Ejercicios alternativos</h3>
          <ul className="mt-3 flex flex-col gap-3">
            {exercise.related_exercises.map((related) => (
              <li
                key={related.related_exercise_id}
                className="flex gap-4 rounded-lg border border-slate-700 bg-slate-800/50 p-4"
              >
                {related.related_exercise_thumbnail_url &&
                  (onSelectExercise ? (
                    <button
                      type="button"
                      onClick={() => onSelectExercise(related.related_exercise_id)}
                      className="shrink-0"
                    >
                      <img
                        src={related.related_exercise_thumbnail_url}
                        alt=""
                        loading="lazy"
                        className="h-16 w-24 rounded-md object-cover"
                      />
                    </button>
                  ) : (
                    <Link to={`/ejercicios/${related.related_exercise_id}`} className="shrink-0">
                      <img
                        src={related.related_exercise_thumbnail_url}
                        alt=""
                        loading="lazy"
                        className="h-16 w-24 rounded-md object-cover"
                      />
                    </Link>
                  ))}
                <div className="min-w-0">
                  {onSelectExercise ? (
                    <button
                      type="button"
                      onClick={() => onSelectExercise(related.related_exercise_id)}
                      className="text-left font-medium text-indigo-400 transition-colors hover:text-indigo-300"
                    >
                      {related.related_exercise_name}
                    </button>
                  ) : (
                    <Link
                      to={`/ejercicios/${related.related_exercise_id}`}
                      className="font-medium text-indigo-400 transition-colors hover:text-indigo-300"
                    >
                      {related.related_exercise_name}
                    </Link>
                  )}
                  {related.note && <p className="mt-1 text-sm text-slate-300">{related.note}</p>}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default ExerciseDetailContent
