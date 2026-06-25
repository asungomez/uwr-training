import type { components } from '@/api/schema'

import { formatSecondsAsTime } from './seriesFormat'

type ItemResponse = components['schemas']['ItemResponse']

/** A series item's populated prescription fields, in display order, as label/value
 *  pairs. Only the fields the admin filled in are returned. Shared by the training
 *  detail view and the register (start session) flow. */
export function prescriptionFields(item: ItemResponse): { label: string; value: string }[] {
  const fields: { label: string; value: string }[] = []
  if (item.sets != null) fields.push({ label: 'Series', value: String(item.sets) })
  if (item.reps != null) fields.push({ label: 'Reps/serie', value: String(item.reps) })
  if (item.duration_seconds != null)
    fields.push({ label: 'Tiempo por serie', value: formatSecondsAsTime(item.duration_seconds) })
  if (item.distance_meters != null)
    fields.push({ label: 'Distancia', value: `${item.distance_meters} m` })
  if (item.effort) fields.push({ label: 'Intensidad', value: item.effort })
  return fields
}
