import { useMutation, useQueryClient } from '@tanstack/react-query'
import { removeDragons } from '../lib/api'
import { requireStoredSessionToken } from './useAddDragons'

export function useRemoveDragons() {
  const queryClient = useQueryClient()

  return useMutation<{ removed: string[] }, Error, string[] | undefined>({
    mutationFn: async (codes) => {
      const token = requireStoredSessionToken()
      return await removeDragons(token, codes)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dragons', 'cove'] })
      queryClient.invalidateQueries({ queryKey: ['dragons', 'geode'] })
    },
  })
}

