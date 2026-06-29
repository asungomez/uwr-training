import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { useToast } from '@/components/toast/context'
import { RoleBadge, StatusBadge } from '@/components/features/users/userBadges'
import RegeneratedInvitationModal from '@/components/features/users/RegeneratedInvitationModal'
import ResetCodeModal from '@/components/features/users/ResetCodeModal'

function formatDate(value: string): string {
  return new Date(value).toLocaleString('es-ES', {
    dateStyle: 'long',
    timeStyle: 'short',
  })
}

const BLANK = '—'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1 border-b border-slate-800 py-3 sm:flex-row sm:gap-4">
      <dt className="text-sm font-medium text-slate-400 sm:w-48 sm:shrink-0">{label}</dt>
      <dd className="text-slate-100">{children}</dd>
    </div>
  )
}

function UserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const entryId = id ?? ''
  const { data, isLoading, error } = useQuery('/auth/users/{entry_id}', {
    params: { path: { entry_id: entryId } },
  })
  const mutate = useMutate()
  const toast = useToast()
  const [updating, setUpdating] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [regeneratedToken, setRegeneratedToken] = useState<string | null>(null)
  const [resetCode, setResetCode] = useState<string | null>(null)

  // Only real users can be (de)activated; invitations can be regenerated.
  const isUser = data?.status === 'active' || data?.status === 'inactive'
  const isInvitation =
    data?.status === 'invitation_pending' || data?.status === 'invitation_expired'

  async function toggleActive() {
    if (!data) return
    const nextStatus = data.status === 'active' ? 'inactive' : 'active'
    setUpdating(true)
    setActionError(null)
    const { error: patchError } = await api.PATCH('/auth/users/{user_id}', {
      params: { path: { user_id: entryId } },
      body: { status: nextStatus },
    })
    setUpdating(false)
    if (patchError) {
      setActionError(errorMessage(patchError))
      return
    }
    toast.success(nextStatus === 'active' ? 'Usuario activado.' : 'Usuario desactivado.')
    await mutate(['/auth/users/{entry_id}', { params: { path: { entry_id: entryId } } }])
  }

  async function regenerateInvitation() {
    setUpdating(true)
    setActionError(null)
    const { data: result, error: postError } = await api.POST(
      '/auth/invitations/{invitation_id}/regenerate',
      { params: { path: { invitation_id: entryId } } },
    )
    setUpdating(false)
    if (postError) {
      setActionError(errorMessage(postError))
      return
    }
    setRegeneratedToken(result.token)
    toast.success('Se ha generado una nueva invitación.')
    // The expiry changed, so refresh the detail.
    await mutate(['/auth/users/{entry_id}', { params: { path: { entry_id: entryId } } }])
  }

  async function generateResetCode() {
    setUpdating(true)
    setActionError(null)
    const { data: result, error: postError } = await api.POST('/auth/users/{user_id}/reset-code', {
      params: { path: { user_id: entryId } },
    })
    setUpdating(false)
    if (postError) {
      setActionError(errorMessage(postError))
      return
    }
    setResetCode(result.code)
    toast.success('Se ha generado un código de verificación.')
  }

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/usuarios" className="transition-colors hover:text-slate-200">
          Usuarios
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{data?.email ?? '…'}</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el usuario.</p>}

      {data && (
        <dl className="mt-6 max-w-2xl">
          <Field label="Correo electrónico">{data.email}</Field>
          <Field label="Rol">
            <RoleBadge role={data.role} />
          </Field>
          <Field label="Estado">
            <StatusBadge status={data.status} />
          </Field>
          <Field label="Creado en">{data.created_at ? formatDate(data.created_at) : BLANK}</Field>
          <Field label="Invitado por">{data.invited_by_email ?? BLANK}</Field>
          <Field label="Invitación expira en">
            {data.expires_at ? formatDate(data.expires_at) : BLANK}
          </Field>
        </dl>
      )}

      {data && (isUser || isInvitation) && (
        <div className="mt-6 flex flex-col gap-2">
          <div className="flex flex-wrap gap-2">
            {isUser && (
              <button
                type="button"
                onClick={() => void toggleActive()}
                disabled={updating}
                className={`rounded-md px-4 py-2 text-sm font-medium text-white transition-colors focus:ring-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 ${
                  data.status === 'active'
                    ? 'bg-red-600 hover:bg-red-500 focus:ring-red-400'
                    : 'bg-green-600 hover:bg-green-500 focus:ring-green-400'
                }`}
              >
                {data.status === 'active' ? 'Desactivar' : 'Activar'}
              </button>
            )}
            {isUser && (
              <button
                type="button"
                onClick={() => void generateResetCode()}
                disabled={updating}
                className="rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
              >
                Generar código de verificación
              </button>
            )}
            {isInvitation && (
              <button
                type="button"
                onClick={() => void regenerateInvitation()}
                disabled={updating}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
              >
                Generar nueva invitación
              </button>
            )}
          </div>
          {actionError && (
            <p role="alert" className="text-sm text-red-400">
              {actionError}
            </p>
          )}
        </div>
      )}

      <RegeneratedInvitationModal
        token={regeneratedToken}
        onClose={() => setRegeneratedToken(null)}
      />
      <ResetCodeModal code={resetCode} onClose={() => setResetCode(null)} />
    </section>
  )
}

export default UserDetailPage
