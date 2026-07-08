import { ChevronRight } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { formatLogDate } from '@/components/features/trainings/logFormat'

interface Props {
  // Which of the two lactic-acid logs this page shows; picks the endpoint + label.
  kind: 'personal-best' | 'test-result'
}

const LABELS: Record<Props['kind'], string> = {
  'personal-best': 'Marca personal',
  'test-result': 'Resultado de la prueba',
}

function LacticAcidTestLogDetailPage({ kind }: Props) {
  const { logId } = useParams<{ logId: string }>()
  const id = logId ?? ''
  const path =
    kind === 'personal-best'
      ? '/lactic-acid-test-logs/personal-best/{log_id}'
      : '/lactic-acid-test-logs/test-result/{log_id}'
  const { data, isLoading, error } = useQuery(path, { params: { path: { log_id: id } } })

  return (
    <section className="max-w-2xl">
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/pruebas/acido-lactico" className="transition-colors hover:text-slate-200">
          Prueba de ácido láctico
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registro</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el registro.</p>}

      {data && (
        <div className="mt-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
            {formatLogDate(data.performed_at)}
          </h1>
          <p className="mt-1 text-slate-400">{LABELS[kind]}</p>
          <p className="mt-3 text-slate-200">
            Tiempo: <span className="font-medium">{data.seconds} s</span>
          </p>
          {data.week_name && (
            <p className="mt-1 text-sm text-slate-400">Semana: {data.week_name}</p>
          )}
        </div>
      )}
    </section>
  )
}

export default LacticAcidTestLogDetailPage
