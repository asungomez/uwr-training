import type { components } from '@/api/schema'
import { cardioSubtypeSlugs } from '@/components/features/cardio/cardioLabels'
import {
  categoryLabels,
  categorySlugs,
  subtypeLabels,
  subtypeSlugs,
} from '@/components/features/trainings/trainingLabels'

type Category = components['schemas']['TrainingCategory']
type Subtype = components['schemas']['TrainingSubtype']
type CardioSubtype = components['schemas']['CardioSubtype']

/** "Gimnasio · Acumulación" — the human label for a week requirement's type. */
export function requirementLabel(category: Category, subtype: Subtype): string {
  return `${categoryLabels[category]} · ${subtypeLabels[subtype]}`
}

/** Link to the destination for a requirement's type. Cardio is its own model with
 *  its own slugs/route; gym & pool share the standard training list; the strength
 *  test links to its own page. */
export function requirementLink(category: Category, subtype: Subtype): string | null {
  // The only test for now is the strength test; link straight to its page.
  if (category === 'test') return '/pruebas/fuerza'
  if (category === 'cardio') {
    // Cardio subtypes are a subset of the shared subtypes; map via cardio slugs.
    const slug = cardioSubtypeSlugs[subtype as CardioSubtype] ?? subtypeSlugs[subtype]
    return `/entrenamientos/cardio/${slug}`
  }
  return `/entrenamientos/${categorySlugs[category]}/${subtypeSlugs[subtype]}`
}
