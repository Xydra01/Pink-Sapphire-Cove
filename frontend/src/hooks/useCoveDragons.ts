import { useQuery } from '@tanstack/react-query'
import type { Dragon } from '../lib/api'
import { fetchCove } from '../lib/api'

export function useCoveDragons() {
  return useQuery<Dragon[], Error>({
    queryKey: ['dragons', 'cove'],
    queryFn: fetchCove,
  })
}

