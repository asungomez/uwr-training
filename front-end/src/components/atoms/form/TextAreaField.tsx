import { forwardRef, type TextareaHTMLAttributes } from 'react'

import { controlClass, errorClass, labelClass } from './fieldStyles'

interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string
  error?: string | undefined
}

/** Labeled textarea with its error message. Forwards the ref for RHF register(). */
const TextAreaField = forwardRef<HTMLTextAreaElement, TextAreaFieldProps>(
  ({ label, error, id, ...rest }, ref) => (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <textarea id={id} ref={ref} className={controlClass} {...rest} />
      {error && <p className={errorClass}>{error}</p>}
    </div>
  ),
)
TextAreaField.displayName = 'TextAreaField'

export default TextAreaField
