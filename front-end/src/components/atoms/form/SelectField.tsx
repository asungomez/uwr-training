import { forwardRef, type SelectHTMLAttributes } from 'react'

import { controlClass, errorClass, labelClass } from './fieldStyles'
import SelectControl, { type SelectOption } from './SelectControl'

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string
  options: SelectOption[]
  error?: string | undefined
}

/** Labeled <select> with its error message. Forwards the ref for RHF register(). */
const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(
  ({ label, options, error, id, ...rest }, ref) => (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <SelectControl
        id={id}
        ref={ref}
        options={options}
        className={`${controlClass} w-full`}
        {...rest}
      />
      {error && <p className={errorClass}>{error}</p>}
    </div>
  ),
)
SelectField.displayName = 'SelectField'

export default SelectField
