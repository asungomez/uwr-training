import { UserPlus } from 'lucide-react'
import { useState } from 'react'

import { useQuery } from '../api/client'
import type { components } from '../api/schema'
import InviteUserModal from './InviteUserModal'

type User = components['schemas']['UserResponse']

const roleLabel: Record<User['role'], string> = {
  admin: 'Administrador',
  member: 'Miembro',
}

function RoleBadge({ role }: { role: User['role'] }) {
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

function StatusBadge({ active }: { active: boolean }) {
  const styles = active
    ? 'bg-green-500/15 text-green-300 ring-green-500/30'
    : 'bg-red-500/15 text-red-300 ring-red-500/30'
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${styles}`}>
      {active ? 'Activo' : 'Inactivo'}
    </span>
  )
}

function UsuariosPage() {
  const { data: users, isLoading, error } = useQuery('/auth/users', {})
  const [inviteOpen, setInviteOpen] = useState(false)

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">Usuarios</h2>
        <button
          type="button"
          onClick={() => setInviteOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <UserPlus size={16} />
          Invitar nuevo usuario
        </button>
      </div>

      <InviteUserModal open={inviteOpen} onClose={() => setInviteOpen(false)} />

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se pudieron cargar los usuarios.</p>}

      {users?.length === 0 && <p className="mt-4 text-slate-400">Todavía no hay usuarios.</p>}

      {users && users.length > 0 && (
        <>
          {/* Desktop: table */}
          <table className="mt-6 hidden w-full border-collapse text-left text-sm md:table">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400">
                <th className="py-2 pr-4 font-medium">Correo electrónico</th>
                <th className="py-2 pr-4 font-medium">Rol</th>
                <th className="py-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-slate-800">
                  <td className="py-3 pr-4 text-slate-200">{user.email}</td>
                  <td className="py-3 pr-4">
                    <RoleBadge role={user.role} />
                  </td>
                  <td className="py-3">
                    <StatusBadge active={user.is_active} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Mobile: stacked cards */}
          <ul className="mt-6 flex flex-col gap-3 md:hidden">
            {users.map((user) => (
              <li
                key={user.id}
                className="flex flex-col gap-2 rounded-lg border border-slate-700 bg-slate-800 p-4"
              >
                <span className="break-all font-medium text-slate-100">{user.email}</span>
                <div className="flex flex-wrap gap-2">
                  <RoleBadge role={user.role} />
                  <StatusBadge active={user.is_active} />
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}

export default UsuariosPage
