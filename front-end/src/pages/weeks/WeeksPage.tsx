import {
  closestCenter,
  DndContext,
  type DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { Plus } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import type { components } from '@/api/schema'
import { useAuth } from '@/auth/context'
import SortableWeekRow from '@/components/features/weeks/SortableWeekRow'
import Pagination from '@/components/molecules/Pagination'
import SearchInput from '@/components/molecules/SearchInput'
import { useToast } from '@/components/toast/context'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useUrlListState } from '@/hooks/useUrlListState'

type Week = components['schemas']['WeekResponse']

const PAGE_SIZE = 10

function WeeksPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()

  const { page, search, setPage, setSearch } = useUrlListState()
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  const { data, isLoading, error } = useQuery(
    '/weeks',
    {
      params: {
        query: {
          page,
          page_size: PAGE_SIZE,
          ...(debouncedSearch ? { search: debouncedSearch } : {}),
        },
      },
    },
    { keepPreviousData: true },
  )

  // Local copy so a drag reorders instantly; resynced when server data changes.
  // `ordered` and `syncedItems` must init from the SAME source: on SPA navigation
  // back to a cached page, `data` is already populated on the first render, so
  // seeding `ordered` with [] here would leave it empty (the sync guard sees them
  // already equal and never runs) → a non-empty list rendered as empty.
  const [ordered, setOrdered] = useState<Week[]>(data?.items ?? [])
  const [syncedItems, setSyncedItems] = useState(data?.items)
  if (data?.items !== syncedItems) {
    setSyncedItems(data?.items)
    setOrdered(data?.items ?? [])
  }

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const canReorder = isAdmin && !debouncedSearch
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = ordered.findIndex((w) => w.id === active.id)
    const to = ordered.findIndex((w) => w.id === over.id)
    if (from === -1 || to === -1) return

    const previous = ordered
    setOrdered(arrayMove(ordered, from, to)) // optimistic

    const absolutePosition = (page - 1) * PAGE_SIZE + to
    const { error: patchError } = await api.PATCH('/weeks/{week_id}/position', {
      params: { path: { week_id: String(active.id) } },
      body: { position: absolutePosition },
    })
    if (patchError) {
      setOrdered(previous) // roll back
      toast.error(errorMessage(patchError))
      return
    }
    await mutate(['/weeks'])
  }

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">Calendario</h2>
        {isAdmin && (
          <Link
            to="/calendario/nueva"
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Plus size={16} />
            Nueva semana
          </Link>
        )}
      </div>

      <p className="mt-2 text-slate-400">Semanas de entrenamiento, en orden.</p>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre…" />
      </div>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se pudieron cargar las semanas.</p>}

      {ordered.length === 0 && !isLoading && (
        <p className="mt-4 text-slate-400">
          {debouncedSearch
            ? 'No hay semanas que coincidan con la búsqueda.'
            : 'Todavía no hay semanas.'}
        </p>
      )}

      {ordered.length > 0 && (
        <>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={(event) => void handleDragEnd(event)}
          >
            <SortableContext
              items={ordered.map((w) => w.id)}
              strategy={verticalListSortingStrategy}
            >
              <ul className="mt-6 flex flex-col gap-3">
                {ordered.map((week) => (
                  <SortableWeekRow
                    key={week.id}
                    week={week}
                    draggable={canReorder}
                    onOpen={() => void navigate(`/calendario/${week.id}`)}
                  />
                ))}
              </ul>
            </SortableContext>
          </DndContext>

          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </section>
  )
}

export default WeeksPage
