import type { components } from '@/api/schema'

import { formatSecondsAsTime, parseOptionalInt, parseTimeToSeconds } from './seriesFormat'
import type { TrainingFormValues } from './TrainingForm'

type TrainingDetail = components['schemas']['TrainingSessionDetailResponse']
type ItemResponse = components['schemas']['ItemResponse']
type ItemInput = components['schemas']['ItemInput']
type BlockInput = components['schemas']['BlockInput']

function itemToFormValue(item: ItemResponse) {
  if (item.kind === 'series') {
    return {
      id: item.id,
      kind: 'series' as const,
      exerciseId: item.exercise_id ?? '',
      exerciseName: item.exercise_name ?? '',
      sets: item.sets != null ? String(item.sets) : '',
      reps: item.reps != null ? String(item.reps) : '',
      time: formatSecondsAsTime(item.duration_seconds),
      distance: item.distance_meters != null ? String(item.distance_meters) : '',
      effort: item.effort ?? '',
      notes: item.text ?? '',
    }
  }
  return { id: item.id, kind: 'note' as const, text: item.text ?? '' }
}

function itemToBody(
  item: TrainingFormValues['blocks'][number]['subBlocks'][number]['items'][number],
): ItemInput {
  if (item.kind === 'series') {
    return {
      kind: 'series',
      exercise_id: item.exerciseId,
      sets: parseOptionalInt(item.sets),
      reps: parseOptionalInt(item.reps),
      duration_seconds: parseTimeToSeconds(item.time),
      distance_meters: parseOptionalInt(item.distance),
      effort: item.effort.trim() || null,
      text: item.notes.trim() || null,
    }
  }
  return { kind: 'note', text: item.text || null }
}

/** Map form values into the create/update request body (notes + series). Shared
 *  by the new and edit pages. */
export function formValuesToBlocks(values: TrainingFormValues): BlockInput[] {
  return values.blocks.map((block) => ({
    name: block.name,
    sub_blocks: block.subBlocks.map((sub) => ({
      name: sub.name,
      notes: sub.notes || null,
      items: sub.items.map(itemToBody),
    })),
  }))
}

/** Map a fetched training (with its blocks) into form default values. Shared by
 *  the edit page and the "copy training" flow on the new page. */
export function trainingToFormValues(data: TrainingDetail): Partial<TrainingFormValues> {
  return {
    title: data.title ?? '',
    blocks: data.blocks.map((block) => ({
      id: block.id,
      name: block.name,
      subBlocks: block.sub_blocks.map((sub) => ({
        id: sub.id,
        name: sub.name,
        notes: sub.notes ?? '',
        items: sub.items.map(itemToFormValue),
      })),
    })),
  }
}
