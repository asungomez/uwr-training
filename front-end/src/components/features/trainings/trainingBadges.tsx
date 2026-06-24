import type { components } from '@/api/schema'

import { categoryLabels, subtypeLabels } from './trainingLabels'

type Category = components['schemas']['TrainingCategory']
type Subtype = components['schemas']['TrainingSubtype']

const categoryStyles: Record<Category, string> = {
  gym: 'bg-amber-500/20 text-amber-200 ring-amber-500/40',
  pool: 'bg-sky-500/20 text-sky-200 ring-sky-500/40',
  cardio: 'bg-rose-500/20 text-rose-200 ring-rose-500/40',
}

export function CategoryBadge({ category }: { category: Category }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${categoryStyles[category]}`}
    >
      {categoryLabels[category]}
    </span>
  )
}

export function SubtypeBadge({ subtype }: { subtype: Subtype }) {
  return (
    <span className="inline-flex rounded-full bg-slate-500/15 px-2 py-0.5 text-xs font-medium text-slate-300 ring-1 ring-slate-500/30">
      {subtypeLabels[subtype]}
    </span>
  )
}
