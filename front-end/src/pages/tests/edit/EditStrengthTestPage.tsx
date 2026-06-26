import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import StrengthTestForm from '@/components/features/strengthTest/StrengthTestForm'
import {
  formValuesToItems,
  type StrengthTestFormValues,
  strengthTestToFormValues,
} from '@/components/features/strengthTest/strengthTestFormValues'
import { useToast } from '@/components/toast/context'

function EditStrengthTestPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  const { data, isLoading, error } = useQuery('/strength-test', {})

  async function handleSubmit(values: StrengthTestFormValues) {
    setRootError(undefined)
    const { error: putError } = await api.PUT('/strength-test', {
      body: { items: formValuesToItems(values) },
    })
    if (putError) {
      setRootError(errorMessage(putError))
      return
    }
    toast.success('Prueba de fuerza actualizada.')
    await mutate(['/strength-test'])
    void navigate('/pruebas/fuerza')
  }

  return (
    <section className="max-w-2xl">
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/pruebas/fuerza" className="transition-colors hover:text-slate-200">
          Prueba de fuerza
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Editar</span>
      </nav>

      <h1 className="mt-6 text-2xl font-semibold tracking-tight text-slate-100">
        Editar prueba de fuerza
      </h1>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha podido cargar la prueba.</p>}

      {data && (
        <div className="mt-6">
          <StrengthTestForm
            onSubmit={handleSubmit}
            defaultValues={strengthTestToFormValues(data)}
            rootError={rootError}
          />
        </div>
      )}
    </section>
  )
}

export default EditStrengthTestPage
