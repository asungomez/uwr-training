import { X } from 'lucide-react'
import { useEffect, type ReactNode } from 'react'

// Desktop max-width per size. Mobile is always full-screen regardless.
const sizeClass = {
  md: 'sm:max-w-md',
  lg: 'sm:max-w-lg',
  xl: 'sm:max-w-3xl',
} as const

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  /** Desktop width. Defaults to 'md'; use a larger size for content like editors. */
  size?: keyof typeof sizeClass
  /** Close when clicking the backdrop. Default true; set false for forms where a
   *  stray click (e.g. while selecting editor text) shouldn't discard progress. */
  closeOnBackdrop?: boolean
}

function Modal({
  open,
  onClose,
  title,
  children,
  size = 'md',
  closeOnBackdrop = true,
}: ModalProps) {
  useEffect(() => {
    if (!open) return
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    // Lock background scroll while the (full-screen, on mobile) modal is open.
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return (
    // Mobile: the panel fills the screen (items-stretch, no padding). Desktop: a
    // centered card with a backdrop around it.
    <div
      className="fixed inset-0 z-40 flex items-stretch justify-center bg-black/60 sm:items-center sm:p-4"
      onClick={closeOnBackdrop ? onClose : undefined}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`flex h-full w-full flex-col bg-slate-800 shadow-xl sm:h-auto sm:max-h-[90dvh] sm:rounded-xl sm:border sm:border-slate-700 ${sizeClass[size]}`}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex shrink-0 items-center justify-between border-b border-slate-700 px-4 py-4 sm:border-0 sm:px-6 sm:pt-6 sm:pb-4">
          <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <X size={20} />
          </button>
        </div>
        {/* Scrollable body: scrolls when content is taller than the screen.
            min-h-0 lets this flex child shrink below its content height (else it
            overflows the panel's max-height instead of scrolling). */}
        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4 sm:px-6 sm:pb-6">{children}</div>
      </div>
    </div>
  )
}

export default Modal
