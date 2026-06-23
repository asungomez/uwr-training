import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { errorMessage } from '@/api/errors'
import { useAuth } from '@/auth/context'
import FormError from '@/components/atoms/form/FormError'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import TextField from '@/components/atoms/form/TextField'

const schema = z.object({
  email: z.email('Introduce un correo electrónico válido'),
  password: z.string().min(1, 'La contraseña es obligatoria'),
})

type LoginValues = z.infer<typeof schema>

function LoginForm() {
  const { login } = useAuth()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(schema) })

  async function onSubmit(values: LoginValues) {
    try {
      await login(values.email, values.password)
    } catch (error) {
      setError('root', { message: errorMessage(error) })
    }
  }

  return (
    <form
      onSubmit={(event) => void handleSubmit(onSubmit)(event)}
      noValidate
      className="flex w-full max-w-sm flex-col gap-5 rounded-xl border border-slate-700 bg-slate-800 p-8 shadow-xl"
    >
      <TextField
        id="email"
        label="Correo electrónico"
        type="email"
        autoComplete="email"
        placeholder="tu@correo.com"
        error={errors.email?.message}
        {...register('email')}
      />
      <TextField
        id="password"
        label="Contraseña"
        type="password"
        autoComplete="current-password"
        placeholder="••••••••"
        error={errors.password?.message}
        {...register('password')}
      />

      <FormError message={errors.root?.message} />

      <SubmitButton pending={isSubmitting} pendingLabel="Iniciando sesión…">
        Iniciar sesión
      </SubmitButton>
    </form>
  )
}

export default LoginForm
