import { ChevronRight, Plus } from 'lucide-react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useQuery } from '@/api/client'
import type { components } from '@/api/schema'
import { useAuth } from '@/auth/context'
import { SubtypeBadge } from '@/components/features/trainings/trainingBadges'
import {
  categoryFromSlug,
  categoryLabels,
  subtypeLabels,
  subtypesByCategory,
} from '@/components/features/trainings/trainingLabels'
import FilterSelect from '@/components/molecules/FilterSelect'
import Pagination from '@/components/molecules/Pagination'
import SearchInput from '@/components/molecules/SearchInput'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useUrlListState } from '@/hooks/useUrlListState'

const PAGE_SIZE = 10

type TrainingSession = components['schemas']['TrainingSessionResponse']
type Subtype = TrainingSession['subtype']

const BLANK = 'Sin título'

function TrainingsPage() {
  // The route is a static category slug (…/gimnasio); derive it from the path.
  const { pathname } = useLocation()
  const category = categoryFromSlug(pathname.split('/').pop())

  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const navigate = useNavigate()

  const { page, search, setPage, setSearch, getFilter, setFilter } = useUrlListState()
  // Subtypes are scoped to this category.
  const availableSubtypes: readonly Subtype[] = category ? subtypesByCategory[category] : []
  const subtype = getFilter('subtype', availableSubtypes) as Subtype | ''
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  const { data, isLoading, error } = useQuery(
    '/trainings',
    {
      params: {
        query: {
          page,
          page_size: PAGE_SIZE,
          ...(category ? { category } : {}),
          ...(debouncedSearch ? { search: debouncedSearch } : {}),
          ...(subtype ? { subtype } : {}),
        },
      },
    },
    { keepPreviousData: true },
  )

  // An unknown category slug → back to the landing page.
  if (!category) return <Navigate to="/entrenamientos" replace />

  const sessions = data?.items
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{categoryLabels[category]}</span>
      </nav>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">{categoryLabels[category]}</h2>
        {isAdmin && (
          <Link
            to="/entrenamientos/nuevo"
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Plus size={16} />
            Nuevo entrenamiento
          </Link>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={setSearch} placeholder="Buscar por título…" />
        <FilterSelect
          value={subtype}
          onChange={(value) => setFilter('subtype', value)}
          label="Filtrar por subtipo"
          options={[
            { value: '', label: 'Todos los subtipos' },
            ...availableSubtypes.map((value) => ({ value, label: subtypeLabels[value] })),
          ]}
        />
      </div>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se pudieron cargar los entrenamientos.</p>}

      {sessions?.length === 0 && (
        <p className="mt-4 text-slate-400">
          {debouncedSearch || subtype
            ? 'No hay entrenamientos que coincidan con la búsqueda.'
            : 'Todavía no hay entrenamientos en esta categoría.'}
        </p>
      )}

      {sessions && sessions.length > 0 && (
        <>
          {/* Desktop: table */}
          <table className="mt-6 hidden w-full border-collapse text-left text-sm md:table">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400">
                <th className="py-2 pr-4 font-medium">Título</th>
                <th className="py-2 font-medium">Subtipo</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr
                  key={session.id}
                  onClick={() => void navigate(`/entrenamientos/${session.id}`)}
                  className="cursor-pointer border-b border-slate-800 transition-colors hover:bg-slate-800/50"
                >
                  <td className="py-3 pr-4 text-slate-200">
                    {session.title ?? <span className="text-slate-500">{BLANK}</span>}
                  </td>
                  <td className="py-3">
                    <SubtypeBadge subtype={session.subtype} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Mobile: stacked cards */}
          <ul className="mt-6 flex flex-col gap-3 md:hidden">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => void navigate(`/entrenamientos/${session.id}`)}
                  className="flex w-full flex-col gap-2 rounded-lg border border-slate-700 bg-slate-800 p-4 text-left transition-colors hover:bg-slate-700"
                >
                  <span className="font-medium text-slate-100">
                    {session.title ?? <span className="text-slate-500">{BLANK}</span>}
                  </span>
                  <SubtypeBadge subtype={session.subtype} />
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

export default TrainingsPage
