import { Info, TriangleAlert } from 'lucide-react'

import Tooltip from '@/components/molecules/Tooltip'

import { formatTargetTime, resolveTargetTime, targetTimeMessages } from './targetTime'

interface TargetTimeValueProps {
  /** The item's target-time formula (over `pb` or `st`). */
  formula: string
  /** Athlete's latest lactic personal best (seconds), or null. */
  personalBest: number | null
  /** Athlete's latest speed-test result (seconds), or null. */
  speedResult: number | null
}

/** The value shown after "Tiempo objetivo:" — the computed time with an info tooltip
 *  citing the source test, or the bare formula with a warning to take that test. The
 *  wording (lactic vs speed) follows the variable the formula references. Shared by the
 *  detail and register views. */
function TargetTimeValue({ formula, personalBest, speedResult }: TargetTimeValueProps) {
  const { variable, sourceValue, seconds } = resolveTargetTime(formula, personalBest, speedResult)

  if (variable !== null && sourceValue !== null && seconds !== null) {
    return (
      <Tooltip label={targetTimeMessages[variable].computed(sourceValue)}>
        <span className="inline-flex items-center gap-1 text-slate-200">
          {formatTargetTime(seconds)} <span className="text-slate-500">({formula})</span>
          <Info size={14} className="text-slate-500" />
        </span>
      </Tooltip>
    )
  }
  if (variable !== null) {
    return (
      <Tooltip label={targetTimeMessages[variable].warning}>
        <span className="inline-flex items-center gap-1 text-amber-300">
          {formula}
          <TriangleAlert size={14} />
        </span>
      </Tooltip>
    )
  }
  // Defensive: a malformed formula (the backend validates on save, so this shouldn't
  // occur) — just show it plainly.
  return <span className="text-slate-200">{formula}</span>
}

export default TargetTimeValue
