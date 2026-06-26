import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import TrainingForm, { type TrainingFormValues } from '@/components/features/trainings/TrainingForm'
import {
  formValuesToBlocks,
  trainingToFormValues,
} from '@/components/features/trainings/trainingFormValues'
import { useToast } from '@/components/toast/context'

/** Admin editor for the speed-test warmup. The warmup is just a pool training
 *  session, so it reuses the same TrainingForm (fixed to pool exercises). */
function EditWarmupPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  const { data, isLoading, error } = useQuery('/speed-test/warmup', {})

  async function handleSubmit(values: TrainingFormValues) {
    setRootError(undefined)
    const { error: putError } = await api.PUT('/speed-test/warmup', {
      body: {
        title: values.title || null,
        blocks: formValuesToBlocks(values),
      },
    })
    if (putError) {
      setRootError(errorMessage(putError))
      return
    }
    toast.success('Calentamiento actualizado.')
    await mutate(['/speed-test/warmup'])
    void navigate('/pruebas/velocidad')
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/pruebas/velocidad" className="transition-colors hover:text-slate-200">
          Prueba de velocidad
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Editar calentamiento</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha podido cargar el calentamiento.</p>}

      {data && (
        <>
          <h2 className="mt-6 text-2xl font-semibold tracking-tight">Editar calentamiento</h2>
          <div className="mt-6">
            <TrainingForm
              onSubmit={handleSubmit}
              exerciseType="pool"
              defaultValues={trainingToFormValues(data)}
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

export default EditWarmupPage
