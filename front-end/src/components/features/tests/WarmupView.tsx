import { useSearchParams } from 'react-router-dom'

import type { components } from '@/api/schema'
import ExercisePanel from '@/components/features/trainings/ExercisePanel'
import TrainingItemView from '@/components/features/trainings/TrainingItemView'

type TrainingDetail = components['schemas']['TrainingSessionDetailResponse']

interface WarmupViewProps {
  warmup: TrainingDetail
}

/** Read-only display of the speed-test warmup session, exactly like the training
 *  detail page (clickable exercises open the side panel), but with no logging — the
 *  athlete just reads it before doing the sprint. */
function WarmupView({ warmup }: WarmupViewProps) {
  // ?ejercicio=<id> opens that exercise in the side panel (replace, so Back leaves
  // the page cleanly), matching the training detail page.
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedExerciseId = searchParams.get('ejercicio')

  function selectExercise(exerciseId: string) {
    setSearchParams(
      (params) => {
        params.set('ejercicio', exerciseId)
        return params
      },
      { replace: true },
    )
  }

  function closeExercise() {
    setSearchParams(
      (params) => {
        params.delete('ejercicio')
        return params
      },
      { replace: true },
    )
  }

  const hasContent = warmup.blocks.some((block) => block.sub_blocks.length > 0)
  if (!hasContent) {
    return <p className="text-sm text-slate-500">Todavía no se ha definido el calentamiento.</p>
  }

  return (
    <div
      className={
        selectedExerciseId
          ? 'lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(0,28rem)] lg:items-start lg:gap-8'
          : ''
      }
    >
      <div className="flex min-w-0 flex-col gap-6">
        {warmup.blocks.map((block) => (
          <div key={block.id}>
            <h3 className="font-semibold text-slate-100">{block.name}</h3>
            {block.sub_blocks.map((sub) => (
              <div key={sub.id} className="mt-3 border-l-2 border-slate-800 pl-4">
                <h4 className="font-medium text-slate-200">{sub.name}</h4>
                {sub.notes && <p className="mt-1 text-sm text-slate-400">{sub.notes}</p>}
                {sub.items.length > 0 && (
                  <ol className="mt-2 flex list-decimal flex-col gap-1 pl-5 text-sm marker:text-slate-500">
                    {sub.items.map((item) => (
                      <TrainingItemView
                        key={item.id}
                        item={item}
                        onSelectExercise={selectExercise}
                      />
                    ))}
                  </ol>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>

      {selectedExerciseId && (
        <ExercisePanel
          exerciseId={selectedExerciseId}
          onClose={closeExercise}
          onSelectExercise={selectExercise}
        />
      )}
    </div>
  )
}

export default WarmupView
