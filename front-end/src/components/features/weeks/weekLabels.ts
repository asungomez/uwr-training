import type { components } from '@/api/schema'

type MesocyclePhase = components['schemas']['MesocyclePhase']

export const phaseLabels: Record<MesocyclePhase, string> = {
  adaptation: 'Adaptación',
  accumulation: 'Acumulación',
  transmutation: 'Transmutación',
  realization: 'Realización',
}

export const orderedPhases: MesocyclePhase[] = [
  'adaptation',
  'accumulation',
  'transmutation',
  'realization',
]

export const phaseOptions: { value: MesocyclePhase; label: string }[] = orderedPhases.map(
  (value) => ({ value, label: phaseLabels[value] }),
)

const phaseTint: Record<MesocyclePhase, string> = {
  adaptation: 'bg-emerald-500/20 text-emerald-200 ring-emerald-500/40',
  accumulation: 'bg-amber-500/20 text-amber-200 ring-amber-500/40',
  transmutation: 'bg-sky-500/20 text-sky-200 ring-sky-500/40',
  realization: 'bg-rose-500/20 text-rose-200 ring-rose-500/40',
}

export function phaseBadgeClass(phase: MesocyclePhase): string {
  return phaseTint[phase]
}
