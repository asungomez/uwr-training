import { useState } from 'react'

import type { components } from '@/api/schema'
import FormError from '@/components/atoms/form/FormError'
import SelectField from '@/components/atoms/form/SelectField'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'

import MaterialFileField from './MaterialFileField'
import { categoryLabels } from './materialLabels'

type MaterialCategory = components['schemas']['MaterialCategory']

export interface MaterialFormValues {
  title: string
  category: MaterialCategory
  fileKey: string
}

interface MaterialFormProps {
  onSubmit: (values: MaterialFormValues) => Promise<void>
  defaultValues?: {
    title: string
    category: MaterialCategory
    fileKey: string
    fileName: string | null
  }
  rootError?: string | undefined
  submitLabel?: string
  pendingLabel?: string
}

const categoryOptions = (Object.keys(categoryLabels) as MaterialCategory[]).map((value) => ({
  value,
  label: categoryLabels[value],
}))

function MaterialForm({
  onSubmit,
  defaultValues,
  rootError,
  submitLabel = 'Crear material',
  pendingLabel = 'Creando…',
}: MaterialFormProps) {
  const [title, setTitle] = useState(defaultValues?.title ?? '')
  const [category, setCategory] = useState<MaterialCategory>(defaultValues?.category ?? 'document')
  const [fileKey, setFileKey] = useState<string | null>(defaultValues?.fileKey ?? null)
  const [fileName, setFileName] = useState<string | null>(defaultValues?.fileName ?? null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | undefined>(undefined)

  function changeCategory(next: MaterialCategory) {
    // The upload kind/allowed types differ per category, so a category change
    // clears the chosen file.
    setCategory(next)
    setFileKey(null)
    setFileName(null)
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!title.trim()) {
      setError('El título es obligatorio.')
      return
    }
    if (!fileKey) {
      setError('Sube un archivo.')
      return
    }
    setError(undefined)
    setSubmitting(true)
    await onSubmit({ title: title.trim(), category, fileKey })
    setSubmitting(false)
  }

  return (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      noValidate
      className="flex max-w-md flex-col gap-4"
    >
      <TextField
        id="material-title"
        label="Título"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
      />
      <SelectField
        id="material-category"
        label="Categoría"
        options={categoryOptions}
        value={category}
        onChange={(event) => changeCategory(event.target.value as MaterialCategory)}
      />
      <MaterialFileField
        category={category}
        value={fileKey}
        onChange={setFileKey}
        fileName={fileName}
        onFileNameChange={setFileName}
      />

      <FormError message={error ?? rootError} />
      <div className="flex flex-col gap-1">
        <SubmitButton pending={submitting} pendingLabel={pendingLabel}>
          {submitLabel}
        </SubmitButton>
      </div>
    </form>
  )
}

export default MaterialForm
