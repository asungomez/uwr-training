import { UserPlus } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useQuery } from '@/api/client'
import type { components } from '@/api/schema'
import FilterSelect from '@/components/molecules/FilterSelect'
import Pagination from '@/components/molecules/Pagination'
import SearchInput from '@/components/molecules/SearchInput'
import { RoleBadge, StatusBadge } from '@/components/features/users/userBadges'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import InviteUserModal from '@/components/features/users/InviteUserModal'

const PAGE_SIZE = 10

type DirectoryEntry = components['schemas']['DirectoryEntryResponse']
type Role = DirectoryEntry['role']
type Status = DirectoryEntry['status']

function UsersPage() {
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
  const navigate = useNavigate()

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
                <tr
                  key={entry.id}
                  onClick={() => void navigate(`/usuarios/${entry.id}`)}
                  className="cursor-pointer border-b border-slate-800 transition-colors hover:bg-slate-800/50"
                >
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
              <li key={entry.id}>
                <button
                  type="button"
                  onClick={() => void navigate(`/usuarios/${entry.id}`)}
                  className="flex w-full flex-col gap-2 rounded-lg border border-slate-700 bg-slate-800 p-4 text-left transition-colors hover:bg-slate-700"
                >
                  <span className="break-all font-medium text-slate-100">{entry.email}</span>
                  <div className="flex flex-wrap gap-2">
                    <RoleBadge role={entry.role} />
                    <StatusBadge status={entry.status} />
                  </div>
                </button>
              </li>
            ))}
          </ul>

          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </section>
  )
}

export default UsersPage
