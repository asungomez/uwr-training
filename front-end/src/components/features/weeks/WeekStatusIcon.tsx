import { CircleCheck, CircleDashed } from 'lucide-react'

import type { components } from '@/api/schema'

import { weekStatus } from './weekStatus'

type RequirementProgress = components['schemas']['RequirementProgress']

interface WeekStatusIconProps {
  requirements: RequirementProgress[]
  size?: number
}

/** Green check when a week is fully completed, a dashed circle while in progress,
 *  nothing when not started. */
function WeekStatusIcon({ requirements, size = 18 }: WeekStatusIconProps) {
  const status = weekStatus(requirements)
  if (status === 'completed') {
    return <CircleCheck size={size} className="text-emerald-400" aria-label="Completada" />
  }
  if (status === 'in-progress') {
    return <CircleDashed size={size} className="text-amber-400" aria-label="En progreso" />
  }
  return null
}

export default WeekStatusIcon
