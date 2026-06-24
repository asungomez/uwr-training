import { z } from 'zod'

import type { components } from '@/api/schema'

import {
  formatSecondsAsTime,
  parseOptionalInt,
  parseTimeToSeconds,
} from '@/components/features/trainings/seriesFormat'

type CardioDetail = components['schemas']['CardioTrainingDetailResponse']
type CardioItemResponse = components['schemas']['CardioItemResponse']
type CardioItemInput = components['schemas']['CardioItemInput']

// Form schema. Durations are mm:ss strings; numeric fields are strings, parsed at
// the API boundary. Items are a discriminated union of notes and blocks; a block's
// intervals are a discriminated union of efforts and rests.
const intervalSchema = z.discriminatedUnion('kind', [
  z.object({
    id: z.string(),
    kind: z.literal('effort'),
    time: z.string().min(1, 'Indica la duración'),
    intensity: z.string(),
  }),
  z.object({
    id: z.string(),
    kind: z.literal('rest'),
    time: z.string().min(1, 'Indica la duración'),
  }),
])

export const cardioFormSchema = z.object({
  title: z.string().trim(),
  items: z.array(
    z.discriminatedUnion('kind', [
      z.object({ id: z.string(), kind: z.literal('note'), text: z.string() }),
      z.object({
        id: z.string(),
        kind: z.literal('block'),
        repeats: z.string(),
        rest: z.string(),
        intervals: z.array(intervalSchema).min(1, 'Un bloque necesita al menos un intervalo'),
      }),
    ]),
  ),
})

export type CardioFormValues = z.infer<typeof cardioFormSchema>
export type IntervalDraft = z.infer<typeof intervalSchema>
export type ItemDraft = CardioFormValues['items'][number]
export type NoteDraft = Extract<ItemDraft, { kind: 'note' }>
export type BlockDraft = Extract<ItemDraft, { kind: 'block' }>

let counter = 0
/** A stable-enough client-side id for list keys + DnD (not the DB id). */
function clientId(): string {
  counter += 1
  return `c${counter}-${Math.random().toString(36).slice(2)}`
}

export function newNote(): NoteDraft {
  return { id: clientId(), kind: 'note', text: '' }
}

export function newEffort(): Extract<IntervalDraft, { kind: 'effort' }> {
  return { id: clientId(), kind: 'effort', time: '', intensity: '' }
}

export function newRest(): Extract<IntervalDraft, { kind: 'rest' }> {
  return { id: clientId(), kind: 'rest', time: '' }
}

export function newBlock(): BlockDraft {
  return { id: clientId(), kind: 'block', repeats: '1', rest: '', intervals: [newEffort()] }
}

// ---- server → form ----------------------------------------------------------

function itemToFormValue(item: CardioItemResponse): ItemDraft {
  if (item.kind === 'block') {
    return {
      id: item.id,
      kind: 'block' as const,
      repeats: String(item.repeats || 1),
      rest: formatSecondsAsTime(item.rest_seconds),
      intervals: item.intervals.map((interval) =>
        interval.kind === 'effort'
          ? {
              id: interval.id,
              kind: 'effort' as const,
              time: formatSecondsAsTime(interval.duration_seconds),
              intensity: interval.intensity_pct != null ? String(interval.intensity_pct) : '',
            }
          : {
              id: interval.id,
              kind: 'rest' as const,
              time: formatSecondsAsTime(interval.duration_seconds),
            },
      ),
    }
  }
  return { id: item.id, kind: 'note' as const, text: item.text ?? '' }
}

export function cardioToFormValues(data: CardioDetail): Partial<CardioFormValues> {
  return {
    title: data.title ?? '',
    items: data.items.map(itemToFormValue),
  }
}

// ---- form → server ----------------------------------------------------------

function itemToBody(item: CardioFormValues['items'][number]): CardioItemInput {
  if (item.kind === 'block') {
    return {
      kind: 'block',
      repeats: Math.max(1, parseOptionalInt(item.repeats) ?? 1),
      rest_seconds: parseTimeToSeconds(item.rest),
      intervals: item.intervals.map((interval) =>
        interval.kind === 'effort'
          ? {
              kind: 'effort' as const,
              duration_seconds: parseTimeToSeconds(interval.time) ?? 0,
              intensity_pct: parseOptionalInt(interval.intensity),
            }
          : {
              kind: 'rest' as const,
              duration_seconds: parseTimeToSeconds(interval.time) ?? 0,
            },
      ),
    }
  }
  // repeats/intervals are required by the generated input type (server defaults
  // them); send the no-op values for a note.
  return { kind: 'note', text: item.text || null, repeats: 1, intervals: [] }
}

export function formValuesToItems(values: CardioFormValues): CardioItemInput[] {
  return values.items.map(itemToBody)
}
