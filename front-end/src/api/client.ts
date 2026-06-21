import createClient from 'openapi-fetch'
import { createQueryHook } from 'swr-openapi'

import type { paths } from './schema'

// Same-origin: requests go to /api, proxied to the back-end. credentials:include
// ensures the HTTP-only session cookie is sent with every request.
const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

export const api = createClient<paths>({
  baseUrl: API_BASE,
  credentials: 'include',
})

export const useQuery = createQueryHook(api, 'api')
