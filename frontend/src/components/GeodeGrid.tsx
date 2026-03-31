import { DragonCard } from './DragonCard'
import { useGeodeDragons } from '../hooks/useGeodeDragons'

export function GeodeGrid() {
  const { data, isLoading, isError, error } = useGeodeDragons()

  if (isLoading) {
    return <p className="grid-status">Scanning the geode for urgent dragons…</p>
  }

  if (isError) {
    return (
      <p className="grid-status grid-status--error">
        Unable to load geode dragons: {(error as Error).message}
      </p>
    )
  }

  if (!data || data.length === 0) {
    return <p className="grid-status">No dragons need emergency crystal care right now.</p>
  }

  return (
    <div className="dragon-grid dragon-grid--geode">
      {data.map((dragon) => (
        <DragonCard key={dragon.dragon_code} dragon={dragon} variant="geode" />
      ))}
    </div>
  )
}

