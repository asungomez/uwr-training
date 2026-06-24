import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api } from '@/api/client'
import { errorMessage } from '@/api/errors'
import type { components } from '@/api/schema'
import TrainingForm, { type TrainingFormValues } from '@/components/features/trainings/TrainingForm'
import { useToast } from '@/components/toast/context'

type Subtype = components['schemas']['TrainingSubtype']

function NewTrainingPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  async function handleSubmit(values: TrainingFormValues) {
    setRootError(undefined)
    const { data, error } = await api.POST('/trainings', {
      body: {
        category: values.category,
        // The form validated this against the category; the API re-checks too.
        subtype: values.subtype as Subtype,
        title: values.title || null,
        blocks: values.blocks.map((block) => ({
          name: block.name,
          sub_blocks: block.subBlocks.map((sub) => ({
            name: sub.name,
            notes: sub.notes || null,
            items: sub.items.map((item) => ({ kind: item.kind, text: item.text || null })),
          })),
        })),
      },
    })
    if (error || !data) {
      setRootError(errorMessage(error))
      return
    }
    toast.success('Entrenamiento creado.')
    void navigate(`/entrenamientos/${data.id}`)
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Nuevo entrenamiento</span>
      </nav>

      <h2 className="mt-6 text-2xl font-semibold tracking-tight">Nuevo entrenamiento</h2>

      <div className="mt-6">
        <TrainingForm onSubmit={handleSubmit} rootError={rootError} />
      </div>
    </section>
  )
}

export default NewTrainingPage
