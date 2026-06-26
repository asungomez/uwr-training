import type { ReactNode } from 'react'

interface TooltipProps {
  /** The hover/focus target. */
  children: ReactNode
  /** The text shown in the bubble. */
  label: string
}

/** A lightweight CSS tooltip: wraps a trigger and reveals `label` on hover or
 *  keyboard focus (no JS state). The trigger is focusable so it works without a
 *  mouse, and the bubble is announced via the trigger's aria-label. */
function Tooltip({ children, label }: TooltipProps) {
  return (
    <span className="group relative inline-flex">
      <span tabIndex={0} aria-label={label} className="inline-flex cursor-help focus:outline-none">
        {children}
      </span>
      <span
        role="tooltip"
        className="pointer-events-none invisible absolute bottom-full left-1/2 z-20 mb-1 w-max max-w-xs -translate-x-1/2 rounded-md border border-slate-600 bg-slate-800 px-2 py-1 text-xs text-slate-100 opacity-0 shadow-lg transition-opacity group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100"
      >
        {label}
      </span>
    </span>
  )
}

export default Tooltip
