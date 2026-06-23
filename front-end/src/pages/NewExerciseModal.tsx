import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { api, useMutate } from '../api/client'
import { errorMessage } from '../api/errors'
import Modal from '../components/Modal'
import { useToast } from '../components/toast/context'

const schema = z.object({
  name: z.string().trim().min(1, 'El nombre es obligatorio'),
  description: z.string().trim(),
  type: z.enum(['gym', 'pool']),
})

type ExerciseValues = z.infer<typeof schema>

interface NewExerciseModalProps {
  open: boolean
  onClose: () => void
}

const fieldClass =
  'rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none'

function NewExerciseModal({ open, onClose }: NewExerciseModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ExerciseValues>({
    resolver: zodResolver(schema),
    defaultValues: { type: 'gym' },
  })
  const toast = useToast()
  const mutate = useMutate()

  function handleClose() {
    reset()
    onClose()
  }

  async function onSubmit(values: ExerciseValues) {
    const { error } = await api.POST('/exercises', {
      body: {
        name: values.name,
        description: values.description || null,
        type: values.type,
      },
    })
    if (error) {
      setError('root', { message: errorMessage(error) })
      return
    }
    toast.success('Ejercicio creado.')
    await mutate(['/exercises'])
    handleClose()
  }

  return (
    <Modal open={open} onClose={handleClose} title="Nuevo ejercicio">
      <form
        onSubmit={(event) => void handleSubmit(onSubmit)(event)}
        noValidate
        className="flex flex-col gap-4"
      >
        <div className="flex flex-col gap-1">
          <label htmlFor="exercise-name" className="text-sm font-medium text-slate-300">
            Nombre
          </label>
          <input id="exercise-name" type="text" {...register('name')} className={fieldClass} />
          {errors.name && <p className="text-sm text-red-400">{errors.name.message}</p>}
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="exercise-description" className="text-sm font-medium text-slate-300">
            Descripción
          </label>
          <textarea
            id="exercise-description"
            rows={3}
            {...register('description')}
            className={fieldClass}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="exercise-type" className="text-sm font-medium text-slate-300">
            Tipo
          </label>
          <select id="exercise-type" {...register('type')} className={fieldClass}>
            <option value="gym">Gimnasio</option>
            <option value="pool">Piscina</option>
          </select>
        </div>

        {errors.root && (
          <p role="alert" className="text-sm text-red-400">
            {errors.root.message}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 rounded-md bg-indigo-600 px-4 py-2 font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? 'Creando…' : 'Crear ejercicio'}
        </button>
      </form>
    </Modal>
  )
}

export default NewExerciseModal
