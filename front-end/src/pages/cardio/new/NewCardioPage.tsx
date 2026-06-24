import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { api, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import {
  type CardioFormValues,
  cardioToFormValues,
  formValuesToItems,
} from '@/components/features/cardio/cardioFormValues'
import CardioForm from '@/components/features/cardio/CardioForm'
import {
  cardioSubtypeFromSlug,
  cardioSubtypeLabels,
  cardioSubtypeSlugs,
} from '@/components/features/cardio/cardioLabels'
import { useToast } from '@/components/toast/context'

function NewCardioPage() {
  // Route: /entrenamientos/cardio/{subtypeSlug}/nuevo — subtype comes from the URL.
  const { pathname } = useLocation()
  const subtypeSlug = pathname.split('/')[3]
  const subtype = cardioSubtypeFromSlug(subtypeSlug)

  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  // ?copiar_de=<id> pre-populates the form with another training's data.
  const [searchParams] = useSearchParams()
  const copyFromId = searchParams.get('copiar_de')

  const { data, isLoading, error } = useQuery(
    '/cardio-trainings/{training_id}',
    copyFromId ? { params: { path: { training_id: copyFromId } } } : null,
  )

  async function handleSubmit(values: CardioFormValues) {
    if (!subtype) return
    setRootError(undefined)
    const { data: created, error: createError } = await api.POST('/cardio-trainings', {
      body: {
        subtype,
        title: values.title || null,
        items: formValuesToItems(values),
      },
    })
    if (createError || !created) {
      setRootError(errorMessage(createError))
      return
    }
    toast.success('Entrenamiento creado.')
    void navigate(`/entrenamientos/cardio/sesion/${created.id}`)
  }

  // Unknown subtype → cardio category landing.
  if (!subtype) return <Navigate to="/entrenamientos/cardio" replace />

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
        <Link
          to={`/entrenamientos/cardio/${cardioSubtypeSlugs[subtype]}`}
          className="transition-colors hover:text-slate-200"
        >
          {cardioSubtypeLabels[subtype]}
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Nuevo entrenamiento</span>
      </nav>

      <h2 className="mt-6 text-2xl font-semibold tracking-tight">
        Nuevo entrenamiento · Cardio / {cardioSubtypeLabels[subtype]}
      </h2>

      {copyFromId && isLoading && <p className="mt-6 text-slate-400">Cargando…</p>}
      {copyFromId && error && (
        <p className="mt-6 text-red-400">No se ha encontrado el entrenamiento a copiar.</p>
      )}

      {(!copyFromId || data) && (
        <div className="mt-6">
          <CardioForm
            onSubmit={handleSubmit}
            {...(data ? { defaultValues: cardioToFormValues(data) } : {})}
            rootError={rootError}
          />
        </div>
      )}
    </section>
  )
}

export default NewCardioPage
