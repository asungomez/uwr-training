import Modal from '@/components/atoms/Modal'
import CopyableValue from '@/components/molecules/CopyableValue'

interface ResetCodeModalProps {
  code: string | null
  onClose: () => void
}

/** Shows a freshly generated password-reset code for the admin to share. */
function ResetCodeModal({ code, onClose }: ResetCodeModalProps) {
  return (
    <Modal open={code !== null} onClose={onClose} title="Código de verificación">
      {code !== null && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-slate-300">
            Comparte este código con la persona para que pueda cambiar su contraseña:
          </p>
          <CopyableValue value={code} label="Código de verificación" />
        </div>
      )}
    </Modal>
  )
}

export default ResetCodeModal
