import { X } from 'lucide-react'
import { useEffect } from 'react'

import { useQuery } from '@/api/client'
import ExerciseDetailContent from '@/components/features/exercises/ExerciseDetailContent'

interface ExercisePanelProps {
  exerciseId: string
  onClose: () => void
  /** Open a different exercise (e.g. clicking a related one) — replaces the view. */
  onSelectExercise: (exerciseId: string) => void
}

/** Shows a full exercise inline while reading a training. Mobile: a full-screen
 *  modal overlay. Desktop (lg+): a sticky right-hand column. Driven by the
 *  ?ejercicio=<id> query param via its owner. */
function ExercisePanel({ exerciseId, onClose, onSelectExercise }: ExercisePanelProps) {
  const { data, isLoading, error } = useQuery('/exercises/{exercise_id}', {
    params: { path: { exercise_id: exerciseId } },
  })

  // Esc closes; lock background scroll only while it's a full-screen overlay
  // (below lg). On desktop it's an in-flow column, so leave scrolling alone.
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    const isOverlay = window.matchMedia('(max-width: 1023px)').matches
    const previousOverflow = document.body.style.overflow
    if (isOverlay) document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [onClose, exerciseId])

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={data?.name ?? 'Ejercicio'}
      className="fixed inset-0 z-40 flex flex-col bg-slate-800 lg:sticky lg:top-6 lg:z-auto lg:h-[calc(100dvh-7rem)] lg:self-start lg:rounded-xl lg:border lg:border-slate-700"
    >
      <div className="flex shrink-0 items-center justify-between border-b border-slate-700 px-4 py-4 lg:px-6">
        <h3 className="text-sm font-medium text-slate-400">Ejercicio</h3>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar"
          className="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <X size={20} />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 lg:px-6">
        {isLoading && <p className="text-slate-400">Cargando…</p>}
        {error && <p className="text-red-400">No se ha encontrado el ejercicio.</p>}
        {data && <ExerciseDetailContent exercise={data} onSelectExercise={onSelectExercise} />}
      </div>
    </div>
  )
}

export default ExercisePanel
