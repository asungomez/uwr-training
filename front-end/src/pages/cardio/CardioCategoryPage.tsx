import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import {
  cardioSubtypeDescriptions,
  cardioSubtypeLabels,
  cardioSubtypeSlugs,
  orderedCardioSubtypes,
} from '@/components/features/cardio/cardioLabels'

const subtypeTint = 'border-slate-600 bg-slate-800/60 hover:border-indigo-500/60 hover:bg-slate-800'

/** The cardio category landing: subtype cards. Mirrors the gym/pool category page
 *  but reads from the separate cardio model. */
function CardioCategoryPage() {
  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Cardio</span>
      </nav>

      <h2 className="mt-4 text-2xl font-semibold tracking-tight">Cardio</h2>
      <p className="mt-2 text-slate-400">Elige un subtipo para ver sus entrenamientos.</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {orderedCardioSubtypes.map((subtype) => (
          <Link
            key={subtype}
            to={`/entrenamientos/cardio/${cardioSubtypeSlugs[subtype]}`}
            className={`flex flex-col gap-2 rounded-lg border p-5 transition-colors ${subtypeTint}`}
          >
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-lg font-semibold text-slate-100">
                {cardioSubtypeLabels[subtype]}
              </h3>
              <ChevronRight size={18} className="text-slate-400" />
            </div>
            <p className="text-sm text-slate-300">{cardioSubtypeDescriptions[subtype]}</p>
          </Link>
        ))}
      </div>
    </section>
  )
}

export default CardioCategoryPage
