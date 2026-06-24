import type { components } from '@/api/schema'

import { phaseBadgeClass, phaseLabels } from './weekLabels'

type MesocyclePhase = components['schemas']['MesocyclePhase']

export function PhaseBadge({ phase }: { phase: MesocyclePhase }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${phaseBadgeClass(phase)}`}
    >
      {phaseLabels[phase]}
    </span>
  )
}
