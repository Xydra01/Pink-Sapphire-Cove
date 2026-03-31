import { useQuery } from '@tanstack/react-query'
import type { Dragon } from '../lib/api'
import { fetchGeode } from '../lib/api'

const GEODE_REFETCH_MS = 45_000

export function useGeodeDragons() {
  return useQuery<Dragon[], Error>({
    queryKey: ['dragons', 'geode'],
    queryFn: fetchGeode,
    refetchInterval: GEODE_REFETCH_MS,
    refetchIntervalInBackground: true,
  })
}

