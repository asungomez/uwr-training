import { forwardRef, type SelectHTMLAttributes } from 'react'

import { controlClass, errorClass, labelClass } from './fieldStyles'

interface Option {
  value: string
  label: string
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string
  options: Option[]
  error?: string | undefined
}

/** Labeled <select> with its error message. Forwards the ref for RHF register(). */
const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(
  ({ label, options, error, id, ...rest }, ref) => (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <select id={id} ref={ref} className={controlClass} {...rest}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className={errorClass}>{error}</p>}
    </div>
  ),
)
SelectField.displayName = 'SelectField'

export default SelectField
