import type { components } from '@/api/schema'

import type { TrainingFormValues } from './TrainingForm'

type TrainingDetail = components['schemas']['TrainingSessionDetailResponse']

/** Map a fetched training (with its blocks) into form default values. Shared by
 *  the edit page and the "copy training" flow on the new page. */
export function trainingToFormValues(data: TrainingDetail): Partial<TrainingFormValues> {
  return {
    title: data.title ?? '',
    category: data.category,
    subtype: data.subtype,
    blocks: data.blocks.map((block) => ({
      id: block.id,
      name: block.name,
      subBlocks: block.sub_blocks.map((sub) => ({
        id: sub.id,
        name: sub.name,
        notes: sub.notes ?? '',
        items: sub.items.map((item) => ({
          id: item.id,
          kind: 'note' as const,
          text: item.text ?? '',
        })),
      })),
    })),
  }
}
