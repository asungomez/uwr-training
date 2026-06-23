import { forwardRef, type InputHTMLAttributes } from 'react'

import { controlClass, errorClass, labelClass } from './fieldStyles'

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string | undefined
}

/** Labeled text input with its error message. Spreads remaining props onto the
 * <input>, and forwards the ref so it plugs straight into RHF register(). */
const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  ({ label, error, id, ...rest }, ref) => (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <input id={id} ref={ref} className={controlClass} {...rest} />
      {error && <p className={errorClass}>{error}</p>}
    </div>
  ),
)
TextField.displayName = 'TextField'

export default TextField
