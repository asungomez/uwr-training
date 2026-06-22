import InvitationLink from '../components/InvitationLink'
import Modal from '../components/Modal'

interface RegeneratedInvitationModalProps {
  token: string | null
  onClose: () => void
}

/** Shows the freshly regenerated invitation link to copy. */
function RegeneratedInvitationModal({ token, onClose }: RegeneratedInvitationModalProps) {
  return (
    <Modal open={token !== null} onClose={onClose} title="Nueva invitación">
      {token !== null && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-slate-300">
            Se ha generado una nueva invitación. Comparte este enlace con la persona invitada:
          </p>
          <InvitationLink token={token} />
        </div>
      )}
    </Modal>
  )
}

export default RegeneratedInvitationModal
