import { ChevronRight } from 'lucide-react'
import { Link, Navigate, useLocation } from 'react-router-dom'

import type { components } from '@/api/schema'
import {
  categoryFromSlug,
  categoryLabels,
  categorySlugs,
  subtypeLabels,
  subtypeSlugs,
  subtypesByCategory,
} from '@/components/features/trainings/trainingLabels'

type Subtype = components['schemas']['TrainingSubtype']

// Hardcoded blurbs (not from the DB) describing each subtype.
const subtypeDescriptions: Record<Subtype, string> = {
  adaptation: 'Base inicial: acondicionamiento general y técnica antes de cargar.',
  accumulation: 'Volumen de trabajo para acumular adaptaciones de fuerza.',
  transmutation: 'Convierte la fuerza acumulada en potencia específica.',
  realization: 'Pico de rendimiento: máxima expresión de fuerza y potencia.',
  endurance: 'Resistencia de larga duración en el agua.',
  anaerobic: 'Esfuerzos intensos con deuda de oxígeno.',
  alactic: 'Esfuerzos máximos y muy breves, sin acumular lactato.',
  aerobic: 'Trabajo cardiovascular sostenido de baja-media intensidad.',
  strength: 'Prueba de fuerza para evaluar el progreso.',
  speed: 'Prueba de velocidad para evaluar el progreso.',
}

const subtypeTint = 'border-slate-600 bg-slate-800/60 hover:border-indigo-500/60 hover:bg-slate-800'

function TrainingsPage() {
  // The route is a static category slug (…/gimnasio); derive it from the path.
  const { pathname } = useLocation()
  const category = categoryFromSlug(pathname.split('/').pop())

  // An unknown category slug → back to the landing page.
  if (!category) return <Navigate to="/entrenamientos" replace />

  const subtypes: readonly Subtype[] = subtypesByCategory[category]

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{categoryLabels[category]}</span>
      </nav>

      <h2 className="mt-4 text-2xl font-semibold tracking-tight">{categoryLabels[category]}</h2>
      <p className="mt-2 text-slate-400">Elige un subtipo para ver sus entrenamientos.</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {subtypes.map((subtype) => (
          <Link
            key={subtype}
            to={`/entrenamientos/${categorySlugs[category]}/${subtypeSlugs[subtype]}`}
            className={`flex flex-col gap-2 rounded-lg border p-5 transition-colors ${subtypeTint}`}
          >
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-lg font-semibold text-slate-100">{subtypeLabels[subtype]}</h3>
              <ChevronRight size={18} className="text-slate-400" />
            </div>
            <p className="text-sm text-slate-300">{subtypeDescriptions[subtype]}</p>
          </Link>
        ))}
      </div>
    </section>
  )
}

export default TrainingsPage
