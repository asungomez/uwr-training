import { Pencil, Play } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { useAuth } from '@/auth/context'
import SpeedTestLogList from '@/components/features/tests/SpeedTestLogList'
import WarmupView from '@/components/features/tests/WarmupView'

// Scoring scale for the 25 m underwater fins sprint: the time (seconds) and its
// rating. Lower time → better score. Starting scale (no admin editing yet).
const SPEED_SCORES: { seconds: string; label: string }[] = [
  { seconds: '>16', label: 'Cari cómo te lo digo' },
  { seconds: '14.5 - 15.5', label: 'Ponte las pilas' },
  { seconds: '13.5 - 14', label: 'Estás cerca' },
  { seconds: '12.5 - 13', label: 'Tiempo objetivo' },
  { seconds: '12', label: 'Bien' },
  { seconds: '11.5', label: 'Muy bien' },
  { seconds: '< 11', label: 'Leyenda' },
]

function SpeedTestPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const warmup = useQuery('/speed-test/warmup', {})

  return (
    <section>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Prueba de velocidad</h1>

      {/* Desktop: two columns — instructions + warmup on the left, scoring table +
          logs on the right. Single column on mobile. */}
      <div className="mt-6 flex flex-col gap-10 lg:grid lg:grid-cols-2 lg:items-start lg:gap-10">
        {/* Left column: actions, explanation, and the warmup to read before the sprint. */}
        <div className="flex min-w-0 flex-col gap-6">
          <div className="flex flex-wrap gap-2">
            <Link
              to="/pruebas/velocidad/registrar"
              className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              <Play size={16} />
              Empezar prueba
            </Link>
            {isAdmin && (
              <Link
                to="/pruebas/velocidad/editar-calentamiento"
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <Pencil size={16} />
                Editar calentamiento
              </Link>
            )}
          </div>

          <div className="flex flex-col gap-4 text-slate-300">
            <p>
              La prueba de velocidad empieza con unos ejercicios de calentamiento. Después, la
              atleta debe hacer un único largo de 25 m, bajo el agua, con aletas y a la máxima
              velocidad posible, y registrar el resultado.
            </p>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-slate-100">Calentamiento</h2>
            <div className="mt-3">
              {warmup.isLoading && <p className="text-sm text-slate-400">Cargando…</p>}
              {warmup.data && <WarmupView warmup={warmup.data} />}
            </div>
          </div>
        </div>

        {/* Right column: the scoring table and the athlete's own logs + graph. */}
        <div className="min-w-0">
          <div className="overflow-hidden rounded-lg border border-slate-700">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-800/60 text-left text-slate-300">
                  <th className="px-4 py-2 font-medium">Tiempo (25 m)</th>
                  <th className="px-4 py-2 font-medium">Valoración</th>
                </tr>
              </thead>
              <tbody>
                {SPEED_SCORES.map((score) => (
                  <tr key={score.seconds} className="border-t border-slate-700">
                    <td className="px-4 py-2 text-slate-200">{score.seconds} s</td>
                    <td className="px-4 py-2 text-slate-400">{score.label}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <SpeedTestLogList />
        </div>
      </div>
    </section>
  )
}

export default SpeedTestPage
