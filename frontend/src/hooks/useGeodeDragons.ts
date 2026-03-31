import { useQuery } from '@tanstack/react-query'
import type { Dragon } from '../lib/api'
import { fetchGeode } from '../lib/api'

export function useGeodeDragons() {
  return useQuery<Dragon[], Error>({
    queryKey: ['dragons', 'geode'],
    queryFn: fetchGeode,
  })
}

