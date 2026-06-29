import { FileCheck2, Loader2, Upload, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { api } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { labelClass } from '@/components/atoms/form/fieldStyles'

import type { components } from '@/api/schema'

import { fileConstraints, uploadKind } from './materialLabels'

type MaterialCategory = components['schemas']['MaterialCategory']

interface MaterialFileFieldProps {
  category: MaterialCategory
  /** Stored S3 object key, or null when there's no file yet. */
  value: string | null
  onChange: (key: string | null) => void
  /** Name of the just-picked file (kept locally for display). */
  fileName: string | null
  onFileNameChange: (name: string | null) => void
}

/** Uploads a material file (document or recorded video) straight to S3 via a
 *  presigned POST, then yields the stored object key. Shows the file name + a
 *  progress/done state and a remove control. */
function MaterialFileField({
  category,
  value,
  onChange,
  fileName,
  onFileNameChange,
}: MaterialFileFieldProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [progress, setProgress] = useState<number | null>(null)
  const [error, setError] = useState<string | undefined>(undefined)

  const { accept, maxBytes, hint } = fileConstraints[category]
  const uploading = progress !== null

  async function handleFile(file: File) {
    setError(undefined)
    if (!accept.includes(file.type)) {
      setError('El tipo de archivo no es válido.')
      return
    }
    if (file.size > maxBytes) {
      setError('El archivo es demasiado grande.')
      return
    }

    // 1) Ask the API for a presigned upload (kind depends on the category).
    const { data, error: presignError } = await api.POST('/materials/media-uploads', {
      body: { kind: uploadKind[category], content_type: file.type },
    })
    if (presignError || !data) {
      setError(errorMessage(presignError))
      return
    }

    // 2) Upload straight to S3 (XHR for progress events). Show the name + bar now.
    onFileNameChange(file.name)
    setProgress(0)
    try {
      await uploadToS3(data.url, data.fields, file, (pct) => setProgress(pct))
    } catch {
      setError('No se ha podido subir el archivo. Inténtalo de nuevo.')
      setProgress(null)
      onFileNameChange(null)
      return
    }
    setProgress(null)
    onChange(data.key)
  }

  function handleRemove() {
    setError(undefined)
    setProgress(null)
    onChange(null)
    onFileNameChange(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="flex flex-col gap-1">
      <span className={labelClass}>Archivo</span>

      {uploading ? (
        // In-progress upload: a real progress bar (matters for big videos).
        <div className="rounded-md border border-slate-600 bg-slate-900 px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-slate-200">
            <Loader2 size={16} className="shrink-0 animate-spin text-slate-400" />
            <span className="min-w-0 flex-1 truncate">{fileName ?? 'Subiendo…'}</span>
            <span className="shrink-0 tabular-nums text-slate-400">{progress}%</span>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-700">
            <div
              className="h-full rounded-full bg-indigo-500 transition-[width] duration-150"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : value ? (
        <div className="flex items-center gap-2 rounded-md border border-slate-600 bg-slate-900 px-4 py-3 text-sm text-slate-200">
          <FileCheck2 size={16} className="text-emerald-400" />
          <span className="min-w-0 flex-1 truncate">{fileName ?? 'Archivo subido'}</span>
          <button
            type="button"
            onClick={handleRemove}
            aria-label="Quitar archivo"
            className="rounded-full p-1 text-slate-400 transition-colors hover:bg-red-600 hover:text-white"
          >
            <X size={16} />
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex items-center gap-2 rounded-md border border-dashed border-slate-600 px-4 py-3 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <Upload size={16} />
          Subir archivo
          <span className="text-xs text-slate-500">({hint})</span>
        </button>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={accept.join(',')}
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) void handleFile(file)
        }}
      />

      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  )
}

/** POST a file to S3 using the presigned fields, reporting upload progress. */
function uploadToS3(
  url: string,
  fields: Record<string, string>,
  file: File,
  onProgress: (pct: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    // S3 requires the policy fields before the file part.
    Object.entries(fields).forEach(([key, val]) => form.append(key, val))
    form.append('file', file)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', url)
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100))
    })
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve()
      else reject(new Error(`Upload failed: ${xhr.status}`))
    })
    xhr.addEventListener('error', () => reject(new Error('Upload failed')))
    xhr.send(form)
  })
}

export default MaterialFileField
