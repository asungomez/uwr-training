import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'

import { api } from '@/api/client'
import { errorMessage } from '@/api/errors'
import FormError from '@/components/atoms/form/FormError'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'
import { useToast } from '@/components/toast/context'

const schema = z
  .object({
    email: z.email('Introduce un correo electrónico válido'),
    password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
    confirmPassword: z.string(),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  })

type AcceptValues = z.infer<typeof schema>

function AcceptInvitationPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const toast = useToast()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<AcceptValues>({ resolver: zodResolver(schema) })

  async function onSubmit(values: AcceptValues) {
    const { error } = await api.POST('/auth/invitations/{token}/accept', {
      params: { path: { token: token ?? '' } },
      body: { email: values.email, password: values.password },
    })
    if (error) {
      setError('root', { message: errorMessage(error) })
      return
    }
    // Account created — send them to the login screen with a confirmation.
    toast.success('Cuenta creada. Ya puedes iniciar sesión.')
    await navigate('/')
  }

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-8 bg-slate-900 px-4 text-slate-100">
      <h1 className="text-4xl font-semibold tracking-tight">UWR entrenamiento</h1>

      <form
        onSubmit={(event) => void handleSubmit(onSubmit)(event)}
        noValidate
        className="flex w-full max-w-sm flex-col gap-5 rounded-xl border border-slate-700 bg-slate-800 p-8 shadow-xl"
      >
        <p className="text-sm text-slate-300">
          Has sido invitado. Completa tus datos para crear tu cuenta.
        </p>

        <TextField
          id="email"
          label="Correo electrónico"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />
        <TextField
          id="password"
          label="Contraseña"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <TextField
          id="confirmPassword"
          label="Repite la contraseña"
          type="password"
          autoComplete="new-password"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />

        <FormError message={errors.root?.message} />

        <SubmitButton pending={isSubmitting} pendingLabel="Creando cuenta…">
          Crear cuenta
        </SubmitButton>
      </form>
    </main>
  )
}

export default AcceptInvitationPage
