import { ChevronRight } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { useQuery } from '../api/client'
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
  const { data, isLoading, error } = useQuery('/auth/users/{entry_id}', {
    params: { path: { entry_id: id ?? '' } },
  })

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
    </section>
  )
}

export default UserDetailPage
