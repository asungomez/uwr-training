import { ChevronRight } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { CategoryBadge, SubtypeBadge } from '@/components/features/trainings/trainingBadges'

const BLANK = 'Sin título'

function TrainingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const trainingId = id ?? ''
  const { data, isLoading, error } = useQuery('/trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{data?.title ?? '…'}</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el entrenamiento.</p>}

      {data && (
        <div className="mt-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
            {data.title ?? <span className="text-slate-500">{BLANK}</span>}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <CategoryBadge category={data.category} />
            <SubtypeBadge subtype={data.subtype} />
          </div>
        </div>
      )}
    </section>
  )
}

export default TrainingDetailPage
