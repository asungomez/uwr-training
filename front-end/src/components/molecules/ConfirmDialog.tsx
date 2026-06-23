import Modal from '@/components/atoms/Modal'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  /** Label for the confirming action (e.g. "Eliminar"). */
  confirmLabel: string
  pending?: boolean
  /** When true, the confirm button uses the danger (red) style. */
  destructive?: boolean
  error?: string | undefined
  onConfirm: () => void
  onCancel: () => void
}

/** A generic confirmation modal: a message plus cancel/confirm actions. */
function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  pending = false,
  destructive = false,
  error,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal open={open} onClose={onCancel} title={title}>
      <div className="flex flex-col gap-4">
        <p className="text-sm text-slate-300">{message}</p>
        {error && (
          <p role="alert" className="text-sm text-red-400">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={pending}
            className="rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={pending}
            className={`rounded-md px-4 py-2 text-sm font-medium text-white transition-colors focus:ring-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 ${
              destructive
                ? 'bg-red-600 hover:bg-red-500 focus:ring-red-400'
                : 'bg-indigo-600 hover:bg-indigo-500 focus:ring-indigo-400'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </Modal>
  )
}

export default ConfirmDialog
