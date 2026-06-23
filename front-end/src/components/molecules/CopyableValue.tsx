import { Check, Copy } from 'lucide-react'
import { useState } from 'react'

interface CopyableValueProps {
  value: string
  label: string
}

/** Read-only value with a copy button. */
function CopyableValue({ value, label }: CopyableValueProps) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(value)
    setCopied(true)
  }

  return (
    <div className="flex gap-2">
      <input
        readOnly
        value={value}
        aria-label={label}
        className="flex-1 rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:outline-none"
      />
      <button
        type="button"
        onClick={() => void copy()}
        className="inline-flex items-center gap-1 rounded-md border border-slate-600 px-3 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-700 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      >
        {copied ? <Check size={16} /> : <Copy size={16} />}
        {copied ? 'Copiado' : 'Copiar'}
      </button>
    </div>
  )
}

export default CopyableValue
