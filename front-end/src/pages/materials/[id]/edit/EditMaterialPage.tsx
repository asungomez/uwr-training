import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import MaterialForm, { type MaterialFormValues } from '@/components/features/materials/MaterialForm'
import { useToast } from '@/components/toast/context'

function EditMaterialPage() {
  const { id } = useParams<{ id: string }>()
  const materialId = id ?? ''
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  const { data, isLoading, error } = useQuery('/materials/{material_id}', {
    params: { path: { material_id: materialId } },
  })

  async function handleSubmit(values: MaterialFormValues) {
    setRootError(undefined)
    const { error: putError } = await api.PUT('/materials/{material_id}', {
      params: { path: { material_id: materialId } },
      body: { title: values.title, category: values.category, file_key: values.fileKey },
    })
    if (putError) {
      setRootError(errorMessage(putError))
      return
    }
    toast.success('Material actualizado.')
    await mutate(['/materials'])
    await mutate(['/materials/{material_id}', { params: { path: { material_id: materialId } } }])
    void navigate(`/materiales/${materialId}`)
  }

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/materiales" className="transition-colors hover:text-slate-200">
          Materiales
        </Link>
        <ChevronRight size={14} />
        {data && (
          <>
            <Link
              to={`/materiales/${materialId}`}
              className="transition-colors hover:text-slate-200"
            >
              {data.title}
            </Link>
            <ChevronRight size={14} />
          </>
        )}
        <span className="text-slate-200">Editar</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el material.</p>}

      {data && (
        <>
          <h2 className="mt-6 text-2xl font-semibold tracking-tight">Editar material</h2>
          <div className="mt-6">
            <MaterialForm
              onSubmit={handleSubmit}
              defaultValues={{
                title: data.title,
                category: data.category,
                fileKey: data.file_key,
                fileName: null,
              }}
              rootError={rootError}
              submitLabel="Guardar cambios"
              pendingLabel="Guardando…"
            />
          </div>
        </>
      )}
    </section>
  )
}

export default EditMaterialPage
