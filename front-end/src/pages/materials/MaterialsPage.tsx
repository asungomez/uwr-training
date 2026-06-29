import { ChevronRight, Download, FileText, Plus, Video } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useQuery } from '@/api/client'
import type { components } from '@/api/schema'
import { useAuth } from '@/auth/context'
import Pagination from '@/components/molecules/Pagination'

type MaterialCategory = components['schemas']['MaterialCategory']
type Material = components['schemas']['MaterialResponse']

const PAGE_SIZE = 10

const rowClass =
  'flex w-full items-center gap-3 rounded-lg border border-slate-700 bg-slate-800 px-4 py-4 text-left transition-colors hover:bg-slate-700 focus:ring-2 focus:ring-indigo-400 focus:outline-none'

/** A document row downloads in place (no detail page needed). */
function DocumentRow({ material }: { material: Material }) {
  return (
    <a
      href={material.file_url ?? undefined}
      target="_blank"
      rel="noopener noreferrer"
      download
      className={rowClass}
    >
      <FileText size={18} className="shrink-0 text-sky-300" />
      <span className="min-w-0 truncate font-medium text-slate-100">{material.title}</span>
      <Download size={16} className="ml-auto shrink-0 text-slate-400" />
    </a>
  )
}

/** A video row opens its detail page (the player). */
function VideoRow({ material, onOpen }: { material: Material; onOpen: () => void }) {
  return (
    <button type="button" onClick={onOpen} className={rowClass}>
      <Video size={18} className="shrink-0 text-rose-300" />
      <span className="min-w-0 truncate font-medium text-slate-100">{material.title}</span>
      <ChevronRight size={16} className="ml-auto shrink-0 text-slate-500" />
    </button>
  )
}

interface SectionProps {
  title: string
  category: MaterialCategory
  emptyText: string
  renderRow: (material: Material) => React.ReactNode
}

/** One category's materials, paginated independently. */
function MaterialSection({ title, category, emptyText, renderRow }: SectionProps) {
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useQuery(
    '/materials',
    { params: { query: { page, page_size: PAGE_SIZE, category } } },
    { keepPreviousData: true },
  )

  const materials = data?.items ?? []
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  return (
    <div className="mt-8">
      <h3 className="text-lg font-semibold text-slate-100">{title}</h3>

      {isLoading && <p className="mt-3 text-sm text-slate-400">Cargando…</p>}
      {error && <p className="mt-3 text-sm text-red-400">No se pudieron cargar los materiales.</p>}
      {data && materials.length === 0 && <p className="mt-3 text-sm text-slate-500">{emptyText}</p>}

      {materials.length > 0 && (
        <>
          <ul className="mt-3 flex flex-col gap-3">
            {materials.map((material) => (
              <li key={material.id}>{renderRow(material)}</li>
            ))}
          </ul>
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </div>
  )
}

function MaterialsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const navigate = useNavigate()

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <span className="text-slate-200">Materiales</span>
      </nav>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">Materiales</h2>
        {isAdmin && (
          <Link
            to="/materiales/nuevo"
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Plus size={16} />
            Nuevo material
          </Link>
        )}
      </div>

      <MaterialSection
        title="Documentos"
        category="document"
        emptyText="Todavía no hay documentos."
        renderRow={(material) => <DocumentRow material={material} />}
      />
      <MaterialSection
        title="Vídeos"
        category="video"
        emptyText="Todavía no hay vídeos."
        renderRow={(material) => (
          <VideoRow
            material={material}
            onOpen={() => void navigate(`/materiales/${material.id}`)}
          />
        )}
      />
    </section>
  )
}

export default MaterialsPage
