import { Pencil, Play } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/auth/context'
import StrengthTestGraphs from '@/components/features/tests/StrengthTestGraphs'
import StrengthTestLogList from '@/components/features/strengthTest/StrengthTestLogList'

function StrengthTestPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  return (
    <section>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Prueba de fuerza</h1>

      <div className="mt-6 flex flex-wrap gap-2">
        <Link
          to="/pruebas/fuerza/registrar"
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <Play size={16} />
          Empezar prueba
        </Link>
        {isAdmin && (
          <Link
            to="/pruebas/fuerza/editar"
            className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Pencil size={16} />
            Editar
          </Link>
        )}
      </div>

      <div className="mt-6 flex max-w-2xl flex-col gap-4 text-slate-300">
        <p>
          Las pruebas de fuerza servirán para guiar el esfuerzo necesario en el entrenamiento de
          gimnasio. Debe hacerse cada ejercicio en una repetición, con la carga máxima posible sin
          perder técnica.
        </p>
        <p>
          La carga objetivo se calculará en base al último peso corporal registrado, y la atleta
          deberá introducir el peso con el que ha hecho el ejercicio.
        </p>
      </div>

      <StrengthTestGraphs />

      <StrengthTestLogList />
    </section>
  )
}

export default StrengthTestPage
