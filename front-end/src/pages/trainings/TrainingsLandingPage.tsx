import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { components } from '@/api/schema'
import {
  categoryLabels,
  categorySlugs,
  orderedCategories,
} from '@/components/features/trainings/trainingLabels'

type Category = components['schemas']['TrainingCategory']

// Hardcoded blurbs (not from the DB) describing each training category.
const categoryDescriptions: Record<Category, string> = {
  gym: 'Trabajo de fuerza y potencia en seco: adaptación, acumulación, transmutación y realización.',
  pool: 'Entrenamiento en agua: resistencia, anaeróbico y aláctico para apnea y velocidad.',
  cardio: 'Acondicionamiento cardiovascular: trabajo aeróbico y anaeróbico.',
}

const categoryTint: Record<Category, string> = {
  gym: 'border-amber-500/30 bg-amber-500/10 hover:border-amber-500/50',
  pool: 'border-sky-500/30 bg-sky-500/10 hover:border-sky-500/50',
  cardio: 'border-rose-500/30 bg-rose-500/10 hover:border-rose-500/50',
}

function TrainingsLandingPage() {
  return (
    <section>
      <h2 className="text-2xl font-semibold tracking-tight">Entrenamientos</h2>
      <p className="mt-2 text-slate-400">Elige una categoría para ver sus entrenamientos.</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {orderedCategories.map((category) => (
          <Link
            key={category}
            to={`/entrenamientos/${categorySlugs[category]}`}
            className={`flex flex-col gap-2 rounded-lg border p-5 transition-colors ${categoryTint[category]}`}
          >
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-lg font-semibold text-slate-100">{categoryLabels[category]}</h3>
              <ChevronRight size={18} className="text-slate-400" />
            </div>
            <p className="text-sm text-slate-300">{categoryDescriptions[category]}</p>
          </Link>
        ))}
      </div>
    </section>
  )
}

export default TrainingsLandingPage
