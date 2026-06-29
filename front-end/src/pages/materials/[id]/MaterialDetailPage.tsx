import { ChevronRight, Download, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { useAuth } from '@/auth/context'
import { categoryLabels } from '@/components/features/materials/materialLabels'
import ConfirmDialog from '@/components/molecules/ConfirmDialog'
import { useToast } from '@/components/toast/context'

function MaterialDetailPage() {
  const { id } = useParams<{ id: string }>()
  const materialId = id ?? ''
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const toast = useToast()
  const mutate = useMutate()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery('/materials/{material_id}', {
    params: { path: { material_id: materialId } },
  })

  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deletePending, setDeletePending] = useState(false)
  const [deleteError, setDeleteError] = useState<string | undefined>(undefined)

  async function confirmDelete() {
    setDeletePending(true)
    setDeleteError(undefined)
    const { error: deleteErr } = await api.DELETE('/materials/{material_id}', {
      params: { path: { material_id: materialId } },
    })
    setDeletePending(false)
    if (deleteErr) {
      setDeleteError(errorMessage(deleteErr))
      return
    }
    toast.success('Material eliminado.')
    await mutate(['/materials'])
    void navigate('/materiales')
  }

  return (
    <section className="max-w-2xl">
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/materiales" className="transition-colors hover:text-slate-200">
          Materiales
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{data?.title ?? '…'}</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el material.</p>}

      {data && (
        <div className="mt-6">
          <h1 className="text-2xl font-semibold tracking-tight break-words text-slate-100">
            {data.title}
          </h1>
          <p className="mt-1 text-sm text-slate-400">{categoryLabels[data.category]}</p>

          <div className="mt-6">
            {data.category === 'video' ? (
              <video
                src={data.file_url ?? undefined}
                controls
                className="w-full rounded-lg border border-slate-700"
              />
            ) : (
              <a
                href={data.file_url ?? undefined}
                target="_blank"
                rel="noopener noreferrer"
                download
                className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <Download size={16} />
                Descargar
              </a>
            )}
          </div>

          {isAdmin && (
            <div className="mt-8 flex flex-wrap gap-2">
              <Link
                to={`/materiales/${materialId}/editar`}
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <Pencil size={16} />
                Editar
              </Link>
              <button
                type="button"
                onClick={() => {
                  setDeleteError(undefined)
                  setConfirmingDelete(true)
                }}
                className="inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 focus:ring-2 focus:ring-red-400 focus:outline-none"
              >
                <Trash2 size={16} />
                Eliminar
              </button>
            </div>
          )}
        </div>
      )}

      {isAdmin && data && (
        <ConfirmDialog
          open={confirmingDelete}
          title="Eliminar material"
          message={`¿Seguro que quieres eliminar «${data.title}»? Esta acción no se puede deshacer.`}
          confirmLabel={deletePending ? 'Eliminando…' : 'Eliminar'}
          pending={deletePending}
          destructive
          error={deleteError}
          onConfirm={() => void confirmDelete()}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
    </section>
  )
}

export default MaterialDetailPage
