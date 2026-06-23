import { CheckCircle2, Info, X, XCircle } from 'lucide-react'
import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'

import { ToastContext, type Toast, type ToastVariant } from './context'

const AUTO_DISMISS_MS = 4000

const variantConfig: Record<ToastVariant, { styles: string; Icon: typeof Info }> = {
  success: { styles: 'border-green-500/40 bg-green-500/15 text-green-200', Icon: CheckCircle2 },
  error: { styles: 'border-red-500/40 bg-red-500/15 text-red-200', Icon: XCircle },
  info: { styles: 'border-slate-600 bg-slate-800 text-slate-200', Icon: Info },
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(0)

  const remove = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const add = useCallback(
    (message: string, variant: ToastVariant) => {
      const id = nextId.current++
      setToasts((current) => [...current, { id, message, variant }])
      setTimeout(() => remove(id), AUTO_DISMISS_MS)
    },
    [remove],
  )

  const value = useMemo(
    () => ({
      success: (message: string) => add(message, 'success'),
      error: (message: string) => add(message, 'error'),
      info: (message: string) => add(message, 'info'),
    }),
    [add],
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 bottom-4 z-50 flex w-full max-w-sm flex-col gap-2">
        {toasts.map((toast) => {
          const { styles, Icon } = variantConfig[toast.variant]
          return (
            <div
              key={toast.id}
              role={toast.variant === 'error' ? 'alert' : 'status'}
              className={`flex items-start gap-2 rounded-lg border px-4 py-3 text-sm shadow-xl ${styles}`}
            >
              <Icon size={18} className="mt-0.5 shrink-0" />
              <span className="flex-1">{toast.message}</span>
              <button
                type="button"
                onClick={() => remove(toast.id)}
                aria-label="Descartar"
                className="shrink-0 rounded p-0.5 transition-colors hover:bg-white/10 focus:outline-none"
              >
                <X size={16} />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
