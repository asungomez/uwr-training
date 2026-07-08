import { Pencil, Play } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { useAuth } from '@/auth/context'
import LacticAcidTestTables from '@/components/features/tests/LacticAcidTestTables'
import WarmupView from '@/components/features/tests/WarmupView'

function LacticAcidTestPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const warmup = useQuery('/lactic-acid-test/warmup', {})

  return (
    <section>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
        Prueba de ácido láctico
      </h1>

      {/* Desktop: two columns — actions, explanation and warmup on the left, the
          interpretation tables on the right. Single column on mobile. */}
      <div className="mt-6 flex flex-col gap-10 lg:grid lg:grid-cols-2 lg:items-start lg:gap-10">
        <div className="flex min-w-0 flex-col gap-6">
          <div className="flex flex-wrap gap-2">
            <Link
              to="/pruebas/acido-lactico/registrar"
              className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              <Play size={16} />
              Empezar prueba
            </Link>
            {isAdmin && (
              <Link
                to="/pruebas/acido-lactico/editar-calentamiento"
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <Pencil size={16} />
                Editar calentamiento
              </Link>
            )}
          </div>

          <div className="flex flex-col gap-4 text-slate-300">
            <p>
              Las pruebas de ácido láctico se hacen en piscina. Consisten en un calentamiento
              previo, y a continuación dos pruebas que pueden hacerse en días distintos.
            </p>
            <p>
              En la primera se harán 50 metros alternando natación en superficie y subacuática, a la
              máxima potencia que se pueda. Se guardará ese valor como la marca personal (en inglés,
              personal best).
            </p>
            <p>
              La segunda prueba será similar a la primera, pero repitiéndola 8 veces y guardando el
              valor del tiempo medio. El objetivo será que el tiempo medio no supere la marca
              personal por más de 5 segundos.
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

        {/* Right column: the interpretation tables (tabs on desktop, dropdown on mobile). */}
        <div className="min-w-0">
          <LacticAcidTestTables />
        </div>
      </div>
    </section>
  )
}

export default LacticAcidTestPage
