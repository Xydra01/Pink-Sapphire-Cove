import { useMutation, useQueryClient } from '@tanstack/react-query'
import { removeDragons } from '../lib/api'
import { getStoredSessionToken } from './useAddDragons'

export function useRemoveDragons() {
  const queryClient = useQueryClient()

  return useMutation<{ removed: string[] }, Error, string[] | undefined>({
    mutationFn: async (codes) => {
      const token = getStoredSessionToken()
      if (!token) {
        throw new Error('No session token found for removal.')
      }
      return await removeDragons(token, codes)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dragons', 'cove'] })
      queryClient.invalidateQueries({ queryKey: ['dragons', 'geode'] })
    },
  })
}

