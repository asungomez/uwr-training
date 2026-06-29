import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { api, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import TrainingForm, { type TrainingFormValues } from '@/components/features/trainings/TrainingForm'
import {
  categoryFromSlug,
  categoryLabels,
  categorySlugs,
  exerciseTypeForCategory,
  subtypeFromSlug,
  subtypeLabels,
} from '@/components/features/trainings/trainingLabels'
import {
  formValuesToBlocks,
  trainingToFormValues,
} from '@/components/features/trainings/trainingFormValues'
import { useToast } from '@/components/toast/context'

function NewTrainingPage() {
  // Route: /entrenamientos/{categorySlug}/{subtypeSlug}/nuevo — scope comes from the
  // URL. The category slug is static in the route tree, so read both from the path.
  const { pathname } = useLocation()
  const [, , categorySlug, subtypeSlug] = pathname.split('/')
  const category = categoryFromSlug(categorySlug)
  const subtype = category ? subtypeFromSlug(category, subtypeSlug) : undefined

  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  // ?copiar_de=<id> pre-populates the form with another training's data.
  const [searchParams] = useSearchParams()
  const copyFromId = searchParams.get('copiar_de')

  const { data, isLoading, error } = useQuery(
    '/trainings/{training_id}',
    copyFromId ? { params: { path: { training_id: copyFromId } } } : null,
  )

  async function handleSubmit(values: TrainingFormValues) {
    if (!category || !subtype) return
    setRootError(undefined)
    const { data: created, error: createError } = await api.POST('/trainings', {
      body: {
        category,
        subtype,
        title: values.title || null,
        blocks: formValuesToBlocks(values),
      },
    })
    if (createError || !created) {
      setRootError(errorMessage(createError))
      return
    }
    toast.success('Entrenamiento creado.')
    void navigate(`/entrenamientos/${created.id}`)
  }

  // Unknown category → landing; unknown subtype (for a valid category) → its category.
  if (!category) return <Navigate to="/entrenamientos" replace />
  if (!subtype) return <Navigate to={`/entrenamientos/${categorySlugs[category]}`} replace />

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
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
        <Link
          to={`/entrenamientos/${categorySlugs[category]}/${subtypeSlug}`}
          className="transition-colors hover:text-slate-200"
        >
          {subtypeLabels[subtype]}
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Nuevo entrenamiento</span>
      </nav>

      <h2 className="mt-6 text-2xl font-semibold tracking-tight">
        Nuevo entrenamiento · {categoryLabels[category]} / {subtypeLabels[subtype]}
      </h2>

      {/* When copying, wait for the source training before mounting the form
          (default values are only read once, at mount). */}
      {copyFromId && isLoading && <p className="mt-6 text-slate-400">Cargando…</p>}
      {copyFromId && error && (
        <p className="mt-6 text-red-400">No se ha encontrado el entrenamiento a copiar.</p>
      )}

      {(!copyFromId || data) && (
        <div className="mt-6">
          <TrainingForm
            onSubmit={handleSubmit}
            exerciseType={exerciseTypeForCategory[category]}
            {...(data ? { defaultValues: trainingToFormValues(data) } : {})}
            rootError={rootError}
          />
        </div>
      )}
    </section>
  )
}

export default NewTrainingPage
