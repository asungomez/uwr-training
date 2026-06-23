import { errorClass } from './fieldStyles'

/** Form-level (root) error alert, e.g. for API failures. Renders nothing when empty. */
function FormError({ message }: { message?: string | undefined }) {
  if (!message) return null
  return (
    <p role="alert" className={errorClass}>
      {message}
    </p>
  )
}

export default FormError
