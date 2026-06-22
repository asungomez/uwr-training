import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '../api/client'
import { errorMessage } from '../api/errors'
import { RoleBadge, StatusBadge } from '../components/userBadges'

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
  const [updating, setUpdating] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  // Only real users can be (de)activated; invitations have no such action.
  const isUser = data?.status === 'active' || data?.status === 'inactive'

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
    await mutate(['/auth/users/{entry_id}', { params: { path: { entry_id: entryId } } }])
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
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

      {data && isUser && (
        <div className="mt-6 flex flex-col gap-2">
          <button
            type="button"
            onClick={() => void toggleActive()}
            disabled={updating}
            className={`w-fit rounded-md px-4 py-2 text-sm font-medium text-white transition-colors focus:ring-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 ${
              data.status === 'active'
                ? 'bg-red-600 hover:bg-red-500 focus:ring-red-400'
                : 'bg-green-600 hover:bg-green-500 focus:ring-green-400'
            }`}
          >
            {data.status === 'active' ? 'Desactivar' : 'Activar'}
          </button>
          {actionError && (
            <p role="alert" className="text-sm text-red-400">
              {actionError}
            </p>
          )}
        </div>
      )}
    </section>
  )
}

export default UserDetailPage
