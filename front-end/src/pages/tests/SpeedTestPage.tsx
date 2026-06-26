import { Pencil, Play } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/auth/context'
import SpeedTestLogList from '@/components/features/tests/SpeedTestLogList'

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

  return (
    <section className="max-w-2xl">
      <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Prueba de velocidad</h1>

      <div className="mt-4 flex flex-col gap-4 text-slate-300">
        <p>
          La prueba de velocidad empieza con unos ejercicios de calentamiento. Después, la atleta
          debe hacer un único largo de 25 m, bajo el agua, con aletas y a la máxima velocidad
          posible, y registrar el resultado.
        </p>
        <p>El tiempo obtenido se valora según la siguiente tabla.</p>
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-slate-700">
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

      <div className="mt-6 flex flex-wrap gap-2">
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

      <SpeedTestLogList />
    </section>
  )
}

export default SpeedTestPage
