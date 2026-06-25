import type { components } from '@/api/schema'

type RequirementProgress = components['schemas']['RequirementProgress']

export type WeekStatus = 'completed' | 'in-progress' | 'not-started'

/** A week's completion status from its requirements: completed when every
 *  requirement is fully met, in-progress when some sessions are logged but not
 *  all, not-started otherwise. */
export function weekStatus(requirements: RequirementProgress[]): WeekStatus {
  if (requirements.length === 0) return 'not-started'
  const done = requirements.reduce((sum, req) => sum + req.completed, 0)
  if (done === 0) return 'not-started'
  return requirements.every((req) => req.completed >= req.count) ? 'completed' : 'in-progress'
}
