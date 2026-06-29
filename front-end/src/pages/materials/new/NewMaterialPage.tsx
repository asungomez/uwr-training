import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, useMutate } from '@/api/client'
import { errorMessage } from '@/api/errors'
import MaterialForm, { type MaterialFormValues } from '@/components/features/materials/MaterialForm'
import { useToast } from '@/components/toast/context'

function NewMaterialPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  async function handleSubmit(values: MaterialFormValues) {
    setRootError(undefined)
    const { error } = await api.POST('/materials', {
      body: { title: values.title, category: values.category, file_key: values.fileKey },
    })
    if (error) {
      setRootError(errorMessage(error))
      return
    }
    toast.success('Material creado.')
    await mutate(['/materials'])
    void navigate('/materiales')
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
        <span className="text-slate-200">Nuevo material</span>
      </nav>

      <h2 className="mt-6 text-2xl font-semibold tracking-tight">Nuevo material</h2>

      <div className="mt-6">
        <MaterialForm onSubmit={handleSubmit} rootError={rootError} />
      </div>
    </section>
  )
}

export default NewMaterialPage
