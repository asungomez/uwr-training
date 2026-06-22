import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { errorMessage } from './api/errors'
import { useAuth } from './auth/context'

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
      <div className="flex flex-col gap-1">
        <label htmlFor="email" className="text-sm font-medium text-slate-300">
          Correo electrónico
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          {...register('email')}
          className="rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          placeholder="tu@correo.com"
        />
        {errors.email && <p className="text-sm text-red-400">{errors.email.message}</p>}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="password" className="text-sm font-medium text-slate-300">
          Contraseña
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          {...register('password')}
          className="rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          placeholder="••••••••"
        />
        {errors.password && <p className="text-sm text-red-400">{errors.password.message}</p>}
      </div>

      {errors.root && (
        <p role="alert" className="text-sm text-red-400">
          {errors.root.message}
        </p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-2 rounded-md bg-indigo-600 px-4 py-2 font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2 focus:ring-offset-slate-800 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Iniciando sesión…' : 'Iniciar sesión'}
      </button>
    </form>
  )
}

export default LoginForm
