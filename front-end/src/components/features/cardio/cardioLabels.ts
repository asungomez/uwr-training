import type { components } from '@/api/schema'

type CardioSubtype = components['schemas']['CardioSubtype']

export const cardioSubtypeLabels: Record<CardioSubtype, string> = {
  aerobic: 'Aeróbico',
  anaerobic: 'Anaeróbico',
  alactic: 'Aláctico',
}

// Hardcoded blurbs (not from the DB) for the subtype cards.
export const cardioSubtypeDescriptions: Record<CardioSubtype, string> = {
  aerobic: 'Trabajo cardiovascular sostenido de baja-media intensidad.',
  anaerobic: 'Esfuerzos intensos con deuda de oxígeno.',
  alactic: 'Esfuerzos máximos y muy breves, sin acumular lactato.',
}

export const orderedCardioSubtypes: CardioSubtype[] = ['aerobic', 'anaerobic', 'alactic']

// Spanish URL slugs (code stays English, URLs are Spanish).
export const cardioSubtypeSlugs: Record<CardioSubtype, string> = {
  aerobic: 'aerobico',
  anaerobic: 'anaerobico',
  alactic: 'alactico',
}

const slugToSubtype: Record<string, CardioSubtype> = Object.fromEntries(
  (Object.keys(cardioSubtypeSlugs) as CardioSubtype[]).map((subtype) => [
    cardioSubtypeSlugs[subtype],
    subtype,
  ]),
)

/** Resolve a URL slug to its cardio subtype, or undefined if it isn't a known one. */
export function cardioSubtypeFromSlug(slug: string | undefined): CardioSubtype | undefined {
  return slug ? slugToSubtype[slug] : undefined
}
