import { Loader2, Upload, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { api } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { labelClass } from './fieldStyles'

type MediaKind = 'thumbnail' | 'video'

// Mirror of the backend constraints (app/storage.py), enforced before presign.
const CONSTRAINTS: Record<MediaKind, { accept: string[]; maxBytes: number; hint: string }> = {
  thumbnail: {
    accept: ['image/jpeg', 'image/png', 'image/webp'],
    maxBytes: 5 * 1024 * 1024,
    hint: 'JPG, PNG o WebP · máx. 5 MB',
  },
  video: {
    accept: ['video/mp4', 'video/webm', 'video/quicktime'],
    maxBytes: 200 * 1024 * 1024,
    hint: 'MP4, WebM o MOV · máx. 200 MB',
  },
}

interface MediaUploadFieldProps {
  label: string
  kind: MediaKind
  /** Stored S3 object key, or null when there's no media. */
  value: string | null
  onChange: (key: string | null) => void
  /** Preview URL for media already saved on the exercise (edit mode). */
  initialPreviewUrl?: string | null | undefined
}

/** Uploads a thumbnail/video straight to S3 via a presigned POST, then yields the
 *  stored object key. Shows a preview with progress and a remove control. */
function MediaUploadField({
  label,
  kind,
  value,
  onChange,
  initialPreviewUrl,
}: MediaUploadFieldProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  // A local object URL for the just-picked file, so we preview without a round-trip.
  const [localPreview, setLocalPreview] = useState<string | null>(null)
  const [progress, setProgress] = useState<number | null>(null)
  const [error, setError] = useState<string | undefined>(undefined)

  const { accept, maxBytes, hint } = CONSTRAINTS[kind]
  // Show the local preview if we just picked one; else the saved one (edit mode).
  const previewUrl = localPreview ?? (value ? initialPreviewUrl : null) ?? null
  const uploading = progress !== null

  function reset() {
    if (localPreview) URL.revokeObjectURL(localPreview)
    setLocalPreview(null)
    setProgress(null)
  }

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

    // 1) Ask the API for a presigned upload.
    const { data, error: presignError } = await api.POST('/exercises/media-uploads', {
      body: { kind, content_type: file.type },
    })
    if (presignError || !data) {
      setError(errorMessage(presignError))
      return
    }

    // 2) Upload straight to S3 with a multipart form (XHR for progress events).
    const preview = URL.createObjectURL(file)
    setLocalPreview(preview)
    setProgress(0)
    try {
      await uploadToS3(data.url, data.fields, file, (pct) => setProgress(pct))
    } catch {
      setError('No se ha podido subir el archivo. Inténtalo de nuevo.')
      reset()
      return
    }
    setProgress(null)
    onChange(data.key)
  }

  function handleRemove() {
    reset()
    setError(undefined)
    onChange(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="flex flex-col gap-1">
      <span className={labelClass}>{label}</span>

      {previewUrl ? (
        <div className="relative w-fit">
          {kind === 'thumbnail' ? (
            <img
              src={previewUrl}
              alt=""
              className="max-h-40 rounded-md border border-slate-600 object-contain"
            />
          ) : (
            <video
              src={previewUrl}
              controls
              className="max-h-48 rounded-md border border-slate-600"
            />
          )}
          {!uploading && (
            <button
              type="button"
              onClick={handleRemove}
              aria-label={`Quitar ${label.toLowerCase()}`}
              className="absolute -top-2 -right-2 rounded-full bg-slate-800 p-1 text-slate-300 ring-1 ring-slate-600 transition-colors hover:bg-red-600 hover:text-white"
            >
              <X size={16} />
            </button>
          )}
          {uploading && (
            <div className="absolute inset-0 flex items-center justify-center rounded-md bg-black/60 text-sm text-white">
              <Loader2 size={16} className="mr-2 animate-spin" />
              {progress}%
            </div>
          )}
        </div>
      ) : (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex items-center gap-2 rounded-md border border-dashed border-slate-600 px-4 py-3 text-sm text-slate-300 transition-colors hover:border-indigo-500 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <Upload size={16} />
          Subir {label.toLowerCase()}
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

export default MediaUploadField
