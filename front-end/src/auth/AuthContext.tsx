import { type ReactNode } from 'react'

import { api, useQuery } from '../api/client'
import { AuthContext } from './context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data, error, isLoading, mutate } = useQuery(
    '/auth/me',
    {},
    {
      shouldRetryOnError: false, // a 401 means "not logged in", not a transient failure
      revalidateOnFocus: false,
    },
  )

  // 401 surfaces as an error; treat any error as "no authenticated user".
  const user = error ? null : (data ?? null)

  async function login(email: string, password: string): Promise<void> {
    const { data: loggedIn, error: loginError } = await api.POST('/auth/login', {
      body: { email, password },
    })
    if (loginError) {
      throw new Error('Credenciales inválidas')
    }
    await mutate(loggedIn, { revalidate: false })
  }

  async function logout(): Promise<void> {
    await api.POST('/auth/logout')
    await mutate(undefined, { revalidate: false })
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
