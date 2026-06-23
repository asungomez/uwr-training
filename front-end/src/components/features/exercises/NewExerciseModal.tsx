import { useState } from 'react'

import { api, useMutate } from '@/api/client'
import { errorMessage } from '@/api/errors'
import Modal from '@/components/atoms/Modal'
import { useToast } from '@/components/toast/context'

import ExerciseForm, { type ExerciseFormValues } from './ExerciseForm'

interface NewExerciseModalProps {
  open: boolean
  onClose: () => void
}

function NewExerciseModal({ open, onClose }: NewExerciseModalProps) {
  const toast = useToast()
  const mutate = useMutate()
  const [rootError, setRootError] = useState<string | undefined>(undefined)

  function handleClose() {
    setRootError(undefined)
    onClose()
  }

  async function handleSubmit(values: ExerciseFormValues) {
    setRootError(undefined)
    const { error } = await api.POST('/exercises', {
      body: {
        name: values.name,
        description: values.description || null,
        type: values.type,
      },
    })
    if (error) {
      setRootError(errorMessage(error))
      return
    }
    toast.success('Ejercicio creado.')
    await mutate(['/exercises'])
    handleClose()
  }

  return (
    <Modal open={open} onClose={handleClose} title="Nuevo ejercicio" size="xl">
      <ExerciseForm onSubmit={handleSubmit} rootError={rootError} />
    </Modal>
  )
}

export default NewExerciseModal
