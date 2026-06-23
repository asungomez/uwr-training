import { Plus } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '../auth/context'
import NewExerciseModal from './NewExerciseModal'

function ExercisesPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [modalOpen, setModalOpen] = useState(false)

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">Ejercicios</h2>
        {isAdmin && (
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Plus size={16} />
            Nuevo ejercicio
          </button>
        )}
      </div>

      {isAdmin && <NewExerciseModal open={modalOpen} onClose={() => setModalOpen(false)} />}

      <p className="mt-4 text-slate-400">No hay ningún ejercicio todavía.</p>
    </section>
  )
}

export default ExercisesPage
