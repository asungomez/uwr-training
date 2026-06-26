import { z } from 'zod'

import type { components } from '@/api/schema'

type WeekDetail = components['schemas']['WeekDetailResponse']
type RequirementInput = components['schemas']['RequirementInput']
type Category = components['schemas']['TrainingCategory']
type Subtype = components['schemas']['TrainingSubtype']

// Form schema. Category/subtype are the select values; count is a string parsed at
// the API boundary. Empty category is the unselected state.
export const weekFormSchema = z.object({
  name: z.string().trim().min(1, 'El nombre es obligatorio'),
  recommendedDate: z.string(),
  phase: z.enum(['adaptation', 'accumulation', 'transmutation', 'realization']),
  requirements: z.array(
    z.object({
      id: z.string(),
      category: z
        .enum(['', 'gym', 'pool', 'cardio', 'test'])
        .refine((value): value is Category => value !== '', {
          message: 'Elige una categoría',
        }),
      subtype: z.string().min(1, 'Elige un subtipo'),
      count: z.string(),
    }),
  ),
})

export type WeekFormValues = z.infer<typeof weekFormSchema>
// The form's working (input) type — category may be the unselected '' until the
// resolver validates. RHF's Control/register are typed against this.
export type WeekFormInput = z.input<typeof weekFormSchema>
export type RequirementDraft = WeekFormValues['requirements'][number]

let counter = 0
function clientId(): string {
  counter += 1
  return `r${counter}-${Math.random().toString(36).slice(2)}`
}

export function newRequirement(): z.input<typeof weekFormSchema>['requirements'][number] {
  return { id: clientId(), category: '', subtype: '', count: '1' }
}

// ---- server → form ----------------------------------------------------------

export function weekToFormValues(data: WeekDetail): Partial<z.input<typeof weekFormSchema>> {
  return {
    name: data.name,
    recommendedDate: data.recommended_date ?? '',
    phase: data.phase,
    requirements: data.requirements.map((req) => ({
      id: req.id,
      category: req.category,
      subtype: req.subtype,
      count: String(req.count),
    })),
  }
}

// ---- form → server ----------------------------------------------------------

export function formValuesToRequirements(values: WeekFormValues): RequirementInput[] {
  return values.requirements.map((req) => ({
    category: req.category,
    subtype: req.subtype as Subtype,
    // A test is a single event — its count is always 1 (the API enforces this too).
    count: req.category === 'test' ? 1 : Math.max(1, Number.parseInt(req.count, 10) || 1),
  }))
}
