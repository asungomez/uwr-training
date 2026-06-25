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
import { ChevronRight, Plus } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import type { components } from '@/api/schema'
import { useAuth } from '@/auth/context'
import {
  cardioSubtypeFromSlug,
  cardioSubtypeLabels,
  cardioSubtypeSlugs,
} from '@/components/features/cardio/cardioLabels'
import SortableCardioRow from '@/components/features/cardio/SortableCardioRow'
import Pagination from '@/components/molecules/Pagination'
import SearchInput from '@/components/molecules/SearchInput'
import { useToast } from '@/components/toast/context'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useUrlListState } from '@/hooks/useUrlListState'

type CardioTraining = components['schemas']['CardioTrainingResponse']

const PAGE_SIZE = 10

function CardioSubtypePage() {
  // Route: /entrenamientos/cardio/{subtypeSlug} — read the subtype from the path.
  const { pathname } = useLocation()
  const subtypeSlug = pathname.split('/')[3]
  const subtype = cardioSubtypeFromSlug(subtypeSlug)

  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()

  const { page, search, setPage, setSearch } = useUrlListState()
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  const { data, isLoading, error } = useQuery(
    '/cardio-trainings',
    {
      params: {
        query: {
          page,
          page_size: PAGE_SIZE,
          ...(subtype ? { subtype } : {}),
          ...(debouncedSearch ? { search: debouncedSearch } : {}),
        },
      },
    },
    { keepPreviousData: true },
  )

  // Local copy so a drag reorders instantly; resynced when server data changes
  // (adjusting state during render avoids a cascading re-render). `ordered` and
  // `syncedItems` must init from the SAME source: on SPA navigation back to a
  // cached page `data` is already populated on the first render, so seeding
  // `ordered` with [] would leave it empty (the guard sees them already equal and
  // never syncs) → a non-empty list rendered as empty.
  const [ordered, setOrdered] = useState<CardioTraining[]>(data?.items ?? [])
  const [syncedItems, setSyncedItems] = useState(data?.items)
  if (data?.items !== syncedItems) {
    setSyncedItems(data?.items)
    setOrdered(data?.items ?? [])
  }

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  // Unknown subtype → cardio category landing.
  if (!subtype) return <Navigate to="/entrenamientos/cardio" replace />

  // Reordering only makes sense on an unfiltered, admin view.
  const canReorder = isAdmin && !debouncedSearch
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = ordered.findIndex((t) => t.id === active.id)
    const to = ordered.findIndex((t) => t.id === over.id)
    if (from === -1 || to === -1) return

    const previous = ordered
    const reordered = arrayMove(ordered, from, to)
    setOrdered(reordered) // optimistic

    const absolutePosition = (page - 1) * PAGE_SIZE + to
    const { error: patchError } = await api.PATCH('/cardio-trainings/{training_id}/position', {
      params: { path: { training_id: String(active.id) } },
      body: { position: absolutePosition },
    })
    if (patchError) {
      setOrdered(previous) // roll back
      toast.error(errorMessage(patchError))
      return
    }
    await mutate(['/cardio-trainings'])
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <Link to="/entrenamientos/cardio" className="transition-colors hover:text-slate-200">
          Cardio
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{cardioSubtypeLabels[subtype]}</span>
      </nav>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">{cardioSubtypeLabels[subtype]}</h2>
        {isAdmin && (
          <Link
            to={`/entrenamientos/cardio/${cardioSubtypeSlugs[subtype]}/nuevo`}
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

      {ordered.length === 0 && !isLoading && (
        <p className="mt-4 text-slate-400">
          {debouncedSearch
            ? 'No hay entrenamientos que coincidan con la búsqueda.'
            : 'Todavía no hay entrenamientos en este subtipo.'}
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
              items={ordered.map((t) => t.id)}
              strategy={verticalListSortingStrategy}
            >
              <ul className="mt-6 flex flex-col gap-3">
                {ordered.map((training) => (
                  <SortableCardioRow
                    key={training.id}
                    training={training}
                    draggable={canReorder}
                    onOpen={() => void navigate(`/entrenamientos/cardio/sesion/${training.id}`)}
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

export default CardioSubtypePage
