import type { components } from '@/api/schema'

type Role = components['schemas']['DirectoryEntryResponse']['role']
type Status = components['schemas']['DirectoryEntryResponse']['status']

const roleLabel: Record<Role, string> = {
  admin: 'Administrador',
  member: 'Miembro',
}

const statusConfig: Record<Status, { label: string; styles: string }> = {
  active: { label: 'Activo', styles: 'bg-green-500/15 text-green-300 ring-green-500/30' },
  inactive: { label: 'Inactivo', styles: 'bg-red-500/15 text-red-300 ring-red-500/30' },
  invitation_pending: {
    label: 'Invitación pendiente',
    styles: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  },
  invitation_expired: {
    label: 'Invitación expirada',
    styles: 'bg-slate-500/15 text-slate-400 ring-slate-500/30',
  },
}

export function RoleBadge({ role }: { role: Role }) {
  const styles =
    role === 'admin'
      ? 'bg-indigo-500/15 text-indigo-300 ring-indigo-500/30'
      : 'bg-slate-500/15 text-slate-300 ring-slate-500/30'
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${styles}`}>
      {roleLabel[role]}
    </span>
  )
}

export function StatusBadge({ status }: { status: Status }) {
  const { label, styles } = statusConfig[status]
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${styles}`}>
      {label}
    </span>
  )
}
