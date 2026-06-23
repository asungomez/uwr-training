import { ChevronDown } from 'lucide-react'
import { forwardRef, type SelectHTMLAttributes } from 'react'

export interface SelectOption {
  value: string
  label: string
}

interface SelectControlProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[]
}

/**
 * The bare select control: a native <select> with its arrow hidden
 * (appearance-none, which otherwise hugs the edge) plus our own ChevronDown
 * with proper spacing. Styling-only — labels/errors/state live in the wrappers
 * (SelectField for forms, FilterSelect for filter bars). Forwards the ref so RHF
 * register() works through it.
 */
const SelectControl = forwardRef<HTMLSelectElement, SelectControlProps>(
  ({ options, className, ...rest }, ref) => (
    <div className="relative">
      <select ref={ref} className={`appearance-none pr-9 ${className ?? ''}`} {...rest}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown
        size={16}
        className="pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-slate-400"
      />
    </div>
  ),
)
SelectControl.displayName = 'SelectControl'

export default SelectControl
