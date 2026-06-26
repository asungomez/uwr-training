import type { components } from '@/api/schema'

type Category = components['schemas']['TrainingCategory']
type Subtype = components['schemas']['TrainingSubtype']
type ExerciseType = components['schemas']['ExerciseType']

// Which exercise type each training category draws from, so the exercise picker
// only offers relevant ones. Cardio has no dedicated type → no filter (null).
export const exerciseTypeForCategory: Record<Category, ExerciseType | null> = {
  gym: 'gym',
  pool: 'pool',
  cardio: null,
  // "test" is a week-level category (strength test); it has no training sessions.
  test: null,
}

export const categoryLabels: Record<Category, string> = {
  gym: 'Gimnasio',
  pool: 'Piscina',
  cardio: 'Cardio',
  test: 'Prueba',
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
  strength: 'Fuerza',
  speed: 'Velocidad',
}

// Which subtypes belong to each category, mirroring SUBTYPES_BY_CATEGORY on the API.
export const subtypesByCategory: Record<Category, Subtype[]> = {
  gym: ['adaptation', 'accumulation', 'transmutation', 'realization'],
  pool: ['endurance', 'anaerobic', 'alactic'],
  cardio: ['aerobic', 'anaerobic', 'alactic'],
  test: ['strength', 'speed'],
}

export const categoryOptions: { value: Category; label: string }[] = (
  Object.keys(categoryLabels) as Category[]
).map((value) => ({ value, label: categoryLabels[value] }))

// Spanish URL slugs for each category (code stays English, URLs are Spanish).
export const categorySlugs: Record<Category, string> = {
  gym: 'gimnasio',
  pool: 'piscina',
  cardio: 'cardio',
  test: 'prueba',
}

const slugToCategory: Record<string, Category> = Object.fromEntries(
  (Object.keys(categorySlugs) as Category[]).map((category) => [categorySlugs[category], category]),
)

/** Resolve a URL slug to its category, or undefined if it isn't a known one. */
export function categoryFromSlug(slug: string | undefined): Category | undefined {
  return slug ? slugToCategory[slug] : undefined
}

// Ordered list for the sidebar / landing cards.
export const orderedCategories: Category[] = ['gym', 'pool', 'cardio']

// Spanish URL slugs for each subtype.
export const subtypeSlugs: Record<Subtype, string> = {
  adaptation: 'adaptacion',
  accumulation: 'acumulacion',
  transmutation: 'transmutacion',
  realization: 'realizacion',
  endurance: 'resistencia',
  anaerobic: 'anaerobico',
  alactic: 'alactico',
  aerobic: 'aerobico',
  strength: 'fuerza',
  speed: 'velocidad',
}

/** Resolve a subtype URL slug to its value, scoped to the category (so a slug only
 *  resolves if it actually belongs to that category — `anaerobico` is shared). */
export function subtypeFromSlug(category: Category, slug: string | undefined): Subtype | undefined {
  if (!slug) return undefined
  return subtypesByCategory[category].find((subtype) => subtypeSlugs[subtype] === slug)
}
