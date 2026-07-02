import { useState } from 'react'

import { useQuery } from '@/api/client'
import type { components } from '@/api/schema'
import SelectControl from '@/components/atoms/form/SelectControl'
import StrengthTestChart from '@/components/features/tests/StrengthTestChart'

type ExerciseHistory = components['schemas']['ExerciseHistory']

/** One exercise's card: its name and result chart. The current target is shown as a
 *  line inside the chart, so it isn't repeated in the header. */
function ExerciseCard({ exercise }: { exercise: ExerciseHistory }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <h3 className="font-medium text-slate-100">{exercise.exercise_name}</h3>
      <div className="mt-3">
        <StrengthTestChart exercise={exercise} />
      </div>
    </div>
  )
}

/** The per-exercise result graphs. One graph per exercise that has results, laid out
 *  4-up on wide screens, 2-up on medium, and — on mobile — a single graph chosen from
 *  a dropdown (instead of a long stack). Exercises with no results yet are omitted. */
function StrengthTestGraphs() {
  const { data } = useQuery('/strength-test-logs/exercise-history', {})
  const withData = (data?.exercises ?? []).filter((exercise) => exercise.history.length > 0)

  // Which exercise the mobile dropdown shows. Default to the first with data.
  const [selectedId, setSelectedId] = useState('')
  const selected = withData.find((exercise) => exercise.exercise_id === selectedId) ?? withData[0]

  if (withData.length === 0) return null

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold text-slate-100">Resultados por ejercicio</h2>

      {/* Mobile: a dropdown to pick one graph, so the page isn't a long stack. */}
      <div className="mt-3 sm:hidden">
        <SelectControl
          value={selected?.exercise_id ?? ''}
          onChange={(event) => setSelectedId(event.target.value)}
          aria-label="Ejercicio"
          className="w-full rounded-md border border-slate-600 bg-slate-900 py-2 pl-3 text-sm text-slate-100 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          options={withData.map((exercise) => ({
            value: exercise.exercise_id,
            label: exercise.exercise_name,
          }))}
        />
        {selected && (
          <div className="mt-3">
            <ExerciseCard exercise={selected} />
          </div>
        )}
      </div>

      {/* Desktop/tablet: a responsive grid, 2-up then 4-up. */}
      <div className="mt-3 hidden gap-4 sm:grid sm:grid-cols-2 xl:grid-cols-4">
        {withData.map((exercise) => (
          <ExerciseCard key={exercise.exercise_id} exercise={exercise} />
        ))}
      </div>
    </div>
  )
}

export default StrengthTestGraphs
