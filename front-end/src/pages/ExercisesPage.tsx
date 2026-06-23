import { Plus } from 'lucide-react'
import { useState } from 'react'

import { useQuery } from '../api/client'
import type { components } from '../api/schema'
import FilterSelect from '../components/FilterSelect'
import Pagination from '../components/Pagination'
import SearchInput from '../components/SearchInput'
import { useAuth } from '../auth/context'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import NewExerciseModal from './NewExerciseModal'

const PAGE_SIZE = 12

type Exercise = components['schemas']['ExerciseResponse']
type ExerciseType = Exercise['type']

const typeConfig: Record<ExerciseType, { label: string; card: string; badge: string }> = {
  gym: {
    label: 'Gimnasio',
    card: 'border-amber-500/30 bg-amber-500/10',
    badge: 'bg-amber-500/20 text-amber-200 ring-amber-500/40',
  },
  pool: {
    label: 'Piscina',
    card: 'border-sky-500/30 bg-sky-500/10',
    badge: 'bg-sky-500/20 text-sky-200 ring-sky-500/40',
  },
}

function ExerciseCard({ exercise }: { exercise: Exercise }) {
  const { label, card, badge } = typeConfig[exercise.type]
  return (
    <article className={`flex flex-col gap-2 rounded-lg border p-4 ${card}`}>
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-slate-100">{exercise.name}</h3>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${badge}`}>
          {label}
        </span>
      </div>
      {exercise.description && <p className="text-sm text-slate-300">{exercise.description}</p>}
    </article>
  )
}

function ExercisesPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [modalOpen, setModalOpen] = useState(false)

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [type, setType] = useState<ExerciseType | ''>('')
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  function handleSearchChange(value: string) {
    setSearch(value)
    setPage(1)
  }

  function handleTypeChange(value: string) {
    setType(value as ExerciseType | '')
    setPage(1)
  }

  const { data, isLoading, error } = useQuery(
    '/exercises',
    {
      params: {
        query: {
          page,
          page_size: PAGE_SIZE,
          ...(debouncedSearch ? { search: debouncedSearch } : {}),
          ...(type ? { type } : {}),
        },
      },
    },
    { keepPreviousData: true },
  )
  const exercises = data?.items
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">Ejercicios</h2>
        {isAdmin && (
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Plus size={16} />
            Nuevo ejercicio
          </button>
        )}
      </div>

      {isAdmin && <NewExerciseModal open={modalOpen} onClose={() => setModalOpen(false)} />}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <SearchInput
          value={search}
          onChange={handleSearchChange}
          placeholder="Buscar por nombre…"
        />
        <FilterSelect
          value={type}
          onChange={handleTypeChange}
          label="Filtrar por tipo"
          options={[
            { value: '', label: 'Todos los tipos' },
            { value: 'gym', label: 'Gimnasio' },
            { value: 'pool', label: 'Piscina' },
          ]}
        />
      </div>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se pudieron cargar los ejercicios.</p>}

      {exercises?.length === 0 && (
        <p className="mt-4 text-slate-400">
          {debouncedSearch || type
            ? 'No hay ejercicios que coincidan con la búsqueda.'
            : 'No hay ningún ejercicio todavía.'}
        </p>
      )}

      {exercises && exercises.length > 0 && (
        <>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {exercises.map((exercise) => (
              <ExerciseCard key={exercise.id} exercise={exercise} />
            ))}
          </div>
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </section>
  )
}

export default ExercisesPage
