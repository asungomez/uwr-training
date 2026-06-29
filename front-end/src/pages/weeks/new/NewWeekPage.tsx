import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api } from '@/api/client'
import { errorMessage } from '@/api/errors'
import WeekForm from '@/components/features/weeks/WeekForm'
import {
  formValuesToRequirements,
  type WeekFormValues,
} from '@/components/features/weeks/weekFormValues'
import { useToast } from '@/components/toast/context'

function NewWeekPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  async function handleSubmit(values: WeekFormValues) {
    setRootError(undefined)
    const { data, error } = await api.POST('/weeks', {
      body: {
        name: values.name,
        recommended_date: values.recommendedDate || null,
        phase: values.phase,
        requirements: formValuesToRequirements(values),
      },
    })
    if (error || !data) {
      setRootError(errorMessage(error))
      return
    }
    toast.success('Semana creada.')
    void navigate(`/calendario/${data.id}`)
  }

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/calendario" className="transition-colors hover:text-slate-200">
          Calendario
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Nueva semana</span>
      </nav>

      <h2 className="mt-6 text-2xl font-semibold tracking-tight">Nueva semana</h2>

      <div className="mt-6">
        <WeekForm onSubmit={handleSubmit} rootError={rootError} />
      </div>
    </section>
  )
}

export default NewWeekPage
