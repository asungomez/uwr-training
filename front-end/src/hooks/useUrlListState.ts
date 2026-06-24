import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * Keeps list state (page, search, named filters) in the URL query string so the
 * view is shareable/repeatable. Writes use `replace` (typing shouldn't spam
 * history) and omit defaults (`page=1`, empty values) to keep URLs clean. New
 * searches/filters reset back to the first page.
 */
export interface UrlListState {
  page: number
  search: string
  setPage: (page: number) => void
  setSearch: (value: string) => void
  /** Reads a filter, validated against `allowed`; unknown values fall back to ''. */
  getFilter: (key: string, allowed: readonly string[]) => string
  setFilter: (key: string, value: string) => void
  /** Set several filters in one URL update (e.g. changing one clears another).
   *  Doing them in separate setFilter calls would clobber each other, since each
   *  reads the same committed params within one event. */
  setFilters: (values: Record<string, string>) => void
}

export function useUrlListState(): UrlListState {
  const [searchParams, setSearchParams] = useSearchParams()

  const update = useCallback(
    (apply: (next: URLSearchParams) => void) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          apply(next)
          return next
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  const page = Math.max(1, Number(searchParams.get('page')) || 1)
  const search = searchParams.get('q') ?? ''

  const setPage = useCallback(
    (value: number) =>
      update((next) => {
        if (value <= 1) next.delete('page')
        else next.set('page', String(value))
      }),
    [update],
  )

  const setSearch = useCallback(
    (value: string) =>
      update((next) => {
        if (value) next.set('q', value)
        else next.delete('q')
        next.delete('page') // a new search changes the result set → page 1
      }),
    [update],
  )

  const getFilter = useCallback(
    (key: string, allowed: readonly string[]) => {
      const value = searchParams.get(key) ?? ''
      return allowed.includes(value) ? value : ''
    },
    [searchParams],
  )

  const setFilter = useCallback(
    (key: string, value: string) =>
      update((next) => {
        if (value) next.set(key, value)
        else next.delete(key)
        next.delete('page')
      }),
    [update],
  )

  const setFilters = useCallback(
    (values: Record<string, string>) =>
      update((next) => {
        for (const [key, value] of Object.entries(values)) {
          if (value) next.set(key, value)
          else next.delete(key)
        }
        next.delete('page')
      }),
    [update],
  )

  return { page, search, setPage, setSearch, getFilter, setFilter, setFilters }
}
