import LoginForm from '../LoginForm'

function LoginPage() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-8 bg-slate-900 px-4 text-slate-100">
      <h1 className="text-4xl font-semibold tracking-tight">UWR entrenamiento</h1>
      <LoginForm />
    </main>
  )
}

export default LoginPage
