import { zodResolver } from '@hookform/resolvers/zod'
import { Check, Copy } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { api } from '../api/client'
import { errorMessage } from '../api/errors'
import Modal from '../components/Modal'

const schema = z.object({
  email: z.email('Introduce un correo electrónico válido'),
})

type InviteValues = z.infer<typeof schema>

interface InviteUserModalProps {
  open: boolean
  onClose: () => void
}

function inviteUrl(token: string): string {
  return `${window.location.origin}/aceptar-invitacion/${token}`
}

function InviteUserModal({ open, onClose }: InviteUserModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<InviteValues>({ resolver: zodResolver(schema) })
  const [link, setLink] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  function handleClose() {
    reset()
    setLink(null)
    setCopied(false)
    onClose()
  }

  async function onSubmit(values: InviteValues) {
    const { data, error } = await api.POST('/auth/invitations', {
      body: { email: values.email },
    })
    if (error) {
      setError('root', { message: errorMessage(error) })
      return
    }
    setLink(inviteUrl(data.token))
  }

  async function copyLink() {
    if (link === null) return
    await navigator.clipboard.writeText(link)
    setCopied(true)
  }

  return (
    <Modal open={open} onClose={handleClose} title="Invitar nuevo usuario">
      {link === null ? (
        <form
          onSubmit={(event) => void handleSubmit(onSubmit)(event)}
          noValidate
          className="flex flex-col gap-4"
        >
          <div className="flex flex-col gap-1">
            <label htmlFor="invite-email" className="text-sm font-medium text-slate-300">
              Correo electrónico
            </label>
            <input
              id="invite-email"
              type="email"
              autoComplete="off"
              {...register('email')}
              className="rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
              placeholder="nuevo@correo.com"
            />
            {errors.email && <p className="text-sm text-red-400">{errors.email.message}</p>}
          </div>

          {errors.root && (
            <p role="alert" className="text-sm text-red-400">
              {errors.root.message}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-indigo-600 px-4 py-2 font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? 'Enviando…' : 'Enviar invitación'}
          </button>
        </form>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-slate-300">
            Invitación creada. Comparte este enlace con la persona invitada:
          </p>
          <div className="flex gap-2">
            <input
              readOnly
              value={link}
              aria-label="Enlace de invitación"
              className="flex-1 rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => void copyLink()}
              className="inline-flex items-center gap-1 rounded-md border border-slate-600 px-3 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-700 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              {copied ? <Check size={16} /> : <Copy size={16} />}
              {copied ? 'Copiado' : 'Copiar'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}

export default InviteUserModal
