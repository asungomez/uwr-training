import type { components } from '@/api/schema'

type MaterialCategory = components['schemas']['MaterialCategory']

export const categoryLabels: Record<MaterialCategory, string> = {
  document: 'Documento',
  video: 'Vídeo',
}

// The media kind to request a presigned upload for, per category.
export const uploadKind: Record<MaterialCategory, 'material_document' | 'material_video'> = {
  document: 'material_document',
  video: 'material_video',
}

// Mirror of the backend constraints (app/storage.py), enforced before presign.
export const fileConstraints: Record<
  MaterialCategory,
  { accept: string[]; maxBytes: number; hint: string }
> = {
  document: {
    accept: [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',
      'text/csv',
    ],
    maxBytes: 50 * 1024 * 1024,
    hint: 'PDF, Word, Excel, PowerPoint… · máx. 50 MB',
  },
  video: {
    accept: ['video/mp4', 'video/webm', 'video/quicktime'],
    maxBytes: 500 * 1024 * 1024,
    hint: 'MP4, WebM o MOV · máx. 500 MB',
  },
}
