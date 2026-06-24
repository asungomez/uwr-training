import { Plus } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/auth/context'

function TrainingsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">Entrenamientos</h2>
        {isAdmin && (
          <Link
            to="/entrenamientos/nuevo"
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Plus size={16} />
            Nuevo entrenamiento
          </Link>
        )}
      </div>

      <p className="mt-2 text-slate-400">Próximamente.</p>
    </section>
  )
}

export default TrainingsPage
