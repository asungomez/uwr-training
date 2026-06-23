import type { components } from '@/api/schema'

type ExerciseType = components['schemas']['ExerciseResponse']['type']

const typeConfig: Record<ExerciseType, { label: string; styles: string }> = {
  gym: { label: 'Gimnasio', styles: 'bg-amber-500/20 text-amber-200 ring-amber-500/40' },
  pool: { label: 'Piscina', styles: 'bg-sky-500/20 text-sky-200 ring-sky-500/40' },
}

export function ExerciseTypeBadge({ type }: { type: ExerciseType }) {
  const { label, styles } = typeConfig[type]
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${styles}`}>
      {label}
    </span>
  )
}
