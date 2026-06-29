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

    // 1) Start a multipart upload.
    const { data: start, error: startError } = await api.POST('/materials/uploads/start', {
      body: { kind: uploadKind[category], content_type: file.type },
    })
    if (startError || !start) {
      setError(errorMessage(startError))
      return
    }

    onFileNameChange(file.name)
    setProgress(0)

    // 2) Upload the file in parts. Progress reflects bytes S3 has accepted: a part's
    //    bytes only count once its PUT resolves (S3 acknowledged it). Within the part
    //    currently in flight we add its live byte progress for a smooth bar.
    const partSize = start.part_size
    const partCount = Math.max(1, Math.ceil(file.size / partSize))
    let completedBytes = 0
    try {
      for (let partNumber = 1; partNumber <= partCount; partNumber++) {
        const begin = (partNumber - 1) * partSize
        const blob = file.slice(begin, Math.min(begin + partSize, file.size))

        const { data: part, error: partError } = await api.POST('/materials/uploads/part', {
          body: { key: start.key, upload_id: start.upload_id, part_number: partNumber },
        })
        if (partError || !part) throw new Error('part url')

        await putPart(part.url, blob, (sentInPart) => {
          const pct = Math.round(((completedBytes + sentInPart) / file.size) * 100)
          setProgress(Math.min(99, pct)) // 100% is reserved for after `complete`
        })
        completedBytes += blob.size
      }

      // 3) Finalize: S3 stitches the parts into one object.
      const { error: completeError } = await api.POST('/materials/uploads/complete', {
        body: { key: start.key, upload_id: start.upload_id },
      })
      if (completeError) throw new Error('complete')
    } catch {
      setError('No se ha podido subir el archivo. Inténtalo de nuevo.')
      setProgress(null)
      onFileNameChange(null)
      // Best-effort cleanup of the half-done multipart upload.
      void api.POST('/materials/uploads/abort', {
        body: { key: start.key, upload_id: start.upload_id },
      })
      return
    }

    setProgress(null)
    onChange(start.key)
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

/** PUT one part to its presigned S3 URL. `onProgress` reports bytes sent for this
 *  part; the promise resolves only once S3 has acknowledged it (the `load` event). */
function putPart(url: string, blob: Blob, onProgress: (sentBytes: number) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', url)
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) onProgress(event.loaded)
    })
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve()
      else reject(new Error(`Upload failed: ${xhr.status}`))
    })
    xhr.addEventListener('error', () => reject(new Error('Upload failed')))
    xhr.send(blob)
  })
}

export default MaterialFileField
