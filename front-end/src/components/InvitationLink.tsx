import { Check, Copy } from 'lucide-react'
import { useState } from 'react'

function inviteUrl(token: string): string {
  return `${window.location.origin}/aceptar-invitacion/${token}`
}

/** Read-only invitation link with a copy button. */
function InvitationLink({ token }: { token: string }) {
  const [copied, setCopied] = useState(false)
  const link = inviteUrl(token)

  async function copyLink() {
    await navigator.clipboard.writeText(link)
    setCopied(true)
  }

  return (
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
  )
}

export default InvitationLink
