import { ChevronRight, Plus } from 'lucide-react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { useAuth } from '@/auth/context'
import {
  categoryFromSlug,
  categoryLabels,
  categorySlugs,
  subtypeFromSlug,
  subtypeLabels,
} from '@/components/features/trainings/trainingLabels'
import Pagination from '@/components/molecules/Pagination'
import SearchInput from '@/components/molecules/SearchInput'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useUrlListState } from '@/hooks/useUrlListState'

const PAGE_SIZE = 10
const BLANK = 'Sin título'

function TrainingSubtypePage() {
  // Route: /entrenamientos/{categorySlug}/{subtypeSlug} — read both from the path.
  const { pathname } = useLocation()
  const [, , categorySlug, subtypeSlug] = pathname.split('/')
  const category = categoryFromSlug(categorySlug)
  const subtype = category ? subtypeFromSlug(category, subtypeSlug) : undefined

  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const navigate = useNavigate()

  const { page, search, setPage, setSearch } = useUrlListState()
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  const { data, isLoading, error } = useQuery(
    '/trainings',
    {
      params: {
        query: {
          page,
          page_size: PAGE_SIZE,
          ...(category ? { category } : {}),
          ...(subtype ? { subtype } : {}),
          ...(debouncedSearch ? { search: debouncedSearch } : {}),
        },
      },
    },
    { keepPreviousData: true },
  )

  // Unknown category → landing; unknown subtype (for a valid category) → its category.
  if (!category) return <Navigate to="/entrenamientos" replace />
  if (!subtype) return <Navigate to={`/entrenamientos/${categorySlugs[category]}`} replace />

  const sessions = data?.items
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <Link
          to={`/entrenamientos/${categorySlugs[category]}`}
          className="transition-colors hover:text-slate-200"
        >
          {categoryLabels[category]}
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{subtypeLabels[subtype]}</span>
      </nav>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">{subtypeLabels[subtype]}</h2>
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
      </div>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se pudieron cargar los entrenamientos.</p>}

      {sessions?.length === 0 && (
        <p className="mt-4 text-slate-400">
          {debouncedSearch
            ? 'No hay entrenamientos que coincidan con la búsqueda.'
            : 'Todavía no hay entrenamientos en este subtipo.'}
        </p>
      )}

      {sessions && sessions.length > 0 && (
        <>
          <ul className="mt-6 flex flex-col gap-3">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => void navigate(`/entrenamientos/${session.id}`)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 p-4 text-left font-medium text-slate-100 transition-colors hover:bg-slate-700"
                >
                  {session.title ?? <span className="text-slate-500">{BLANK}</span>}
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

export default TrainingSubtypePage
