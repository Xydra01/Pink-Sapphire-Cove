import { useQuery } from '@tanstack/react-query'
import type { Dragon } from '../lib/api'
import { fetchCove } from '../lib/api'

const COVE_REFETCH_MS = 45_000

export function useCoveDragons() {
  return useQuery<Dragon[], Error>({
    queryKey: ['dragons', 'cove'],
    queryFn: fetchCove,
    refetchInterval: COVE_REFETCH_MS,
    refetchIntervalInBackground: true,
  })
}

