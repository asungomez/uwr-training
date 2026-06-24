// API errors carry a stable `detail.code`; the UI renders Spanish from these codes
// rather than the API's (English, debug-only) message.

const messages: Record<string, string> = {
  not_authenticated: 'Tu sesión no es válida. Inicia sesión de nuevo.',
  invalid_session: 'Tu sesión ha expirado. Inicia sesión de nuevo.',
  invalid_credentials: 'Correo electrónico o contraseña incorrectos',
  admin_required: 'No tienes permisos para realizar esta acción.',
  user_not_found: 'No se ha encontrado el usuario.',
  invalid_status: 'El estado indicado no es válido.',
  invalid_reset_code: 'El código de verificación no es válido o ha caducado.',
  email_already_exists: 'Ya existe un usuario con este correo electrónico.',
  invitation_already_exists: 'Ya existe una invitación para este correo electrónico.',
  invitation_already_accepted: 'Esta invitación ya ha sido aceptada.',
  invitation_email_mismatch: 'El correo electrónico no coincide con la invitación.',
  exercise_already_exists: 'Ya existe un ejercicio con este nombre.',
  exercise_not_found: 'No se ha encontrado el ejercicio.',
  invalid_media_type: 'El tipo de archivo no es válido.',
  invalid_training_subtype: 'El subtipo no es válido para esa categoría.',
  invalid_related_exercise: 'Alguno de los ejercicios relacionados no es válido.',
  invitation_not_found: 'La invitación no existe o ya fue utilizada.',
  invitation_expired: 'La invitación ha caducado.',
}

const FALLBACK = 'Ha ocurrido un error. Inténtalo de nuevo.'

/** Wraps an API error body so it can be `throw`n while keeping the code/message. */
export class ApiError extends Error {
  readonly body: unknown
  constructor(body: unknown) {
    super(errorMessage(body))
    this.name = 'ApiError'
    this.body = body
  }
}

export function errorCode(error: unknown): string | null {
  // Unwrap an ApiError to its original body, if present.
  const source = error instanceof ApiError ? error.body : error
  const detail = (source as { detail?: unknown } | undefined)?.detail
  const code = (detail as { code?: unknown } | undefined)?.code
  return typeof code === 'string' ? code : null
}

/** Spanish message for an API error, falling back to a generic message. */
export function errorMessage(error: unknown): string {
  const code = errorCode(error)
  return (code !== null ? messages[code] : undefined) ?? FALLBACK
}
