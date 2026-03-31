import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { AddDragonsResult } from '../lib/api'
import { addDragons } from '../lib/api'

const SESSION_TOKEN_KEY = 'gem-cove-session-token'

export function getStoredSessionToken(): string | null {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(SESSION_TOKEN_KEY)
}

export function storeSessionToken(token: string) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(SESSION_TOKEN_KEY, token)
}

export function requireStoredSessionToken(): string {
  const token = getStoredSessionToken()
  if (!token) {
    throw new Error('No session token found. Add dragons first, then you can remove them.')
  }
  return token
}

export function useAddDragons() {
  const queryClient = useQueryClient()

  return useMutation<AddDragonsResult, Error, string[]>({
    mutationFn: async (codes) => {
      const result = await addDragons(codes)
      storeSessionToken(result.session_token)
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dragons', 'cove'] })
      queryClient.invalidateQueries({ queryKey: ['dragons', 'geode'] })
    },
  })
}

