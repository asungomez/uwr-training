import { z } from 'zod'

import type { components } from '@/api/schema'

type StrengthTest = components['schemas']['StrengthTestResponse']
type StrengthTestItemInput = components['schemas']['StrengthTestItemInput']

// Form schema. Each row carries the picked exercise (id + name for display) and the
// multiplier as a string, parsed at the API boundary. Empty exercise = unpicked.
export const strengthTestFormSchema = z.object({
  items: z.array(
    z.object({
      id: z.string(),
      exerciseId: z.string().min(1, 'Elige un ejercicio'),
      exerciseName: z.string(),
      multiplier: z.string(),
    }),
  ),
})

export type StrengthTestFormValues = z.infer<typeof strengthTestFormSchema>
export type StrengthTestFormInput = z.input<typeof strengthTestFormSchema>
export type StrengthTestItemDraft = StrengthTestFormValues['items'][number]

let counter = 0
function clientId(): string {
  counter += 1
  return `sti${counter}-${Math.random().toString(36).slice(2)}`
}

export function newItem(): StrengthTestItemDraft {
  return { id: clientId(), exerciseId: '', exerciseName: '', multiplier: '1' }
}

// ---- server → form ----------------------------------------------------------

export function strengthTestToFormValues(data: StrengthTest): StrengthTestFormInput {
  return {
    items: data.items.map((item) => ({
      id: item.id,
      exerciseId: item.exercise_id,
      exerciseName: item.exercise_name,
      multiplier: String(item.weight_multiplier),
    })),
  }
}

// ---- form → server ----------------------------------------------------------

export function formValuesToItems(values: StrengthTestFormValues): StrengthTestItemInput[] {
  return values.items.map((item) => ({
    exercise_id: item.exerciseId,
    // Accept comma decimals; fall back to 1 for empty/invalid (the API also guards >0).
    weight_multiplier: Math.max(0.01, Number(item.multiplier.replace(',', '.')) || 1),
  }))
}
