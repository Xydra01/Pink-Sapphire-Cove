import { DragonCard } from './DragonCard'
import { useCoveDragons } from '../hooks/useCoveDragons'
import { useRemoveDragons } from '../hooks/useRemoveDragons'

export function CoveGrid() {
  const { data, isLoading, isError, error } = useCoveDragons()
  const removeMutation = useRemoveDragons()

  if (isLoading) {
    return <p className="grid-status">Loading cove dragons…</p>
  }

  if (isError) {
    return (
      <p className="grid-status grid-status--error">
        Unable to load cove dragons: {(error as Error).message}
      </p>
    )
  }

  if (!data || data.length === 0) {
    return <p className="grid-status">No dragons are resting in the Cove yet.</p>
  }

  const density = data.length >= 80 ? 'compact' : 'full'

  return (
    <div className="dragon-grid dragon-grid--cove">
      {data.map((dragon) => (
        <DragonCard
          key={dragon.dragon_code}
          dragon={dragon}
          variant="cove"
          density={density}
          canRemove={dragon.can_remove}
          onRemove={() => removeMutation.mutate([dragon.dragon_code])}
        />
      ))}
    </div>
  )
}

