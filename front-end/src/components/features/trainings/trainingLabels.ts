import type { components } from '@/api/schema'

type Category = components['schemas']['TrainingCategory']
type Subtype = components['schemas']['TrainingSubtype']

export const categoryLabels: Record<Category, string> = {
  gym: 'Gimnasio',
  pool: 'Piscina',
  cardio: 'Cardio',
}

// Spanish label for every subtype value (across all categories).
export const subtypeLabels: Record<Subtype, string> = {
  adaptation: 'Adaptación',
  accumulation: 'Acumulación',
  transmutation: 'Transmutación',
  realization: 'Realización',
  endurance: 'Resistencia',
  anaerobic: 'Anaeróbico',
  alactic: 'Aláctico',
  aerobic: 'Aeróbico',
}

// Which subtypes belong to each category, mirroring SUBTYPES_BY_CATEGORY on the API.
export const subtypesByCategory: Record<Category, Subtype[]> = {
  gym: ['adaptation', 'accumulation', 'transmutation', 'realization'],
  pool: ['endurance', 'anaerobic', 'alactic'],
  cardio: ['aerobic', 'anaerobic'],
}

export const categoryOptions: { value: Category; label: string }[] = (
  Object.keys(categoryLabels) as Category[]
).map((value) => ({ value, label: categoryLabels[value] }))
