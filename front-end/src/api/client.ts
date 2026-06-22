import createClient from 'openapi-fetch'
import { createMutateHook, createQueryHook } from 'swr-openapi'

import type { paths } from './schema'

// Same-origin: requests go to /api, proxied to the back-end. credentials:include
// ensures the HTTP-only session cookie is sent with every request.
const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

export const api = createClient<paths>({
  baseUrl: API_BASE,
  credentials: 'include',
})

// Deep partial-match: does `subset` appear within `value`? Used to match SWR keys
// by path (and optionally a params subset) for revalidation.
function isMatch(value: unknown, subset: unknown): boolean {
  if (subset === value) return true
  if (typeof subset !== 'object' || subset === null) return false
  if (typeof value !== 'object' || value === null) return false
  return Object.entries(subset).every(([key, sub]) =>
    isMatch((value as Record<string, unknown>)[key], sub),
  )
}

export const useQuery = createQueryHook(api, 'api')
export const useMutate = createMutateHook(api, 'api', isMatch)
