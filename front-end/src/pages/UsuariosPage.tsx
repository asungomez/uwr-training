import { UserPlus } from 'lucide-react'
import { useState } from 'react'

import { useQuery } from '../api/client'
import type { components } from '../api/schema'
import FilterSelect from '../components/FilterSelect'
import Pagination from '../components/Pagination'
import SearchInput from '../components/SearchInput'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import InviteUserModal from './InviteUserModal'

const PAGE_SIZE = 10

type DirectoryEntry = components['schemas']['DirectoryEntryResponse']
type Role = DirectoryEntry['role']
type Status = DirectoryEntry['status']

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

function RoleBadge({ role }: { role: Role }) {
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

function StatusBadge({ status }: { status: Status }) {
  const { label, styles } = statusConfig[status]
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${styles}`}>
      {label}
    </span>
  )
}

function UsuariosPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<Role | ''>('')
  const [status, setStatus] = useState<Status | ''>('')
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  // Searching changes the result set, so jump back to the first page.
  function handleSearchChange(value: string) {
    setSearch(value)
    setPage(1)
  }

  function handleRoleChange(value: string) {
    setRole(value as Role | '')
    setPage(1)
  }

  function handleStatusChange(value: string) {
    setStatus(value as Status | '')
    setPage(1)
  }

  const { data, isLoading, error } = useQuery(
    '/auth/users',
    {
      params: {
        query: {
          page,
          page_size: PAGE_SIZE,
          // Omit empties so the SWR key (and request) stays clean.
          ...(debouncedSearch ? { search: debouncedSearch } : {}),
          ...(role ? { role } : {}),
          ...(status ? { status } : {}),
        },
      },
    },
    { keepPreviousData: true },
  )
  const entries = data?.items
  const totalCount = data?.total_count ?? 0
  const pageCount = Math.ceil(totalCount / PAGE_SIZE)
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

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <SearchInput
          value={search}
          onChange={handleSearchChange}
          placeholder="Buscar por correo…"
        />
        <FilterSelect
          value={role}
          onChange={handleRoleChange}
          label="Filtrar por rol"
          options={[
            { value: '', label: 'Todos los roles' },
            { value: 'admin', label: 'Administrador' },
            { value: 'member', label: 'Miembro' },
          ]}
        />
        <FilterSelect
          value={status}
          onChange={handleStatusChange}
          label="Filtrar por estado"
          options={[
            { value: '', label: 'Todos los estados' },
            { value: 'active', label: 'Activo' },
            { value: 'inactive', label: 'Inactivo' },
            { value: 'invitation_pending', label: 'Invitación pendiente' },
            { value: 'invitation_expired', label: 'Invitación expirada' },
          ]}
        />
      </div>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se pudieron cargar los usuarios.</p>}

      {entries?.length === 0 && (
        <p className="mt-4 text-slate-400">
          {debouncedSearch
            ? 'No hay usuarios que coincidan con la búsqueda.'
            : 'Todavía no hay usuarios.'}
        </p>
      )}

      {entries && entries.length > 0 && (
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
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b border-slate-800">
                  <td className="py-3 pr-4 text-slate-200">{entry.email}</td>
                  <td className="py-3 pr-4">
                    <RoleBadge role={entry.role} />
                  </td>
                  <td className="py-3">
                    <StatusBadge status={entry.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Mobile: stacked cards */}
          <ul className="mt-6 flex flex-col gap-3 md:hidden">
            {entries.map((entry) => (
              <li
                key={entry.id}
                className="flex flex-col gap-2 rounded-lg border border-slate-700 bg-slate-800 p-4"
              >
                <span className="break-all font-medium text-slate-100">{entry.email}</span>
                <div className="flex flex-wrap gap-2">
                  <RoleBadge role={entry.role} />
                  <StatusBadge status={entry.status} />
                </div>
              </li>
            ))}
          </ul>

          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </section>
  )
}

export default UsuariosPage
