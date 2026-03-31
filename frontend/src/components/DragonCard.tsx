import type { Dragon } from '../lib/api'
import './DragonCard.css'

type DragonCardProps = {
  dragon: Dragon
  variant?: 'cove' | 'geode'
  canRemove?: boolean
  onRemove?: () => void
}

export function DragonCard({ dragon, variant = 'cove', canRemove = false, onRemove }: DragonCardProps) {
  const classes = ['dragon-card', `dragon-card--${variant}`].join(' ')

  const hours =
    dragon.time_remaining >= 0 ? `${dragon.time_remaining}h left` : dragon.time_remaining === -2 ? 'Faded' : 'Stable'

  return (
    <article className={classes} aria-label={`Dragon ${dragon.dragon_code}`}>
      <header className="dragon-card__header">
        <span className="dragon-card__code">{dragon.dragon_code}</span>
        {dragon.is_sick && <span className="dragon-card__badge">Urgent</span>}
      </header>
      <div className="dragon-card__body">
        <div className="dragon-card__stat">
          <span className="dragon-card__label">Views</span>
          <span className="dragon-card__value">{dragon.views.toLocaleString()}</span>
        </div>
        <div className="dragon-card__stat">
          <span className="dragon-card__label">Unique</span>
          <span className="dragon-card__value">{dragon.unique_clicks.toLocaleString()}</span>
        </div>
        <div className="dragon-card__stat">
          <span className="dragon-card__label">Time</span>
          <span className="dragon-card__value">{hours}</span>
        </div>
      </div>
      {canRemove && onRemove && (
        <button type="button" className="dragon-card__remove" onClick={onRemove}>
          Remove
        </button>
      )}
    </article>
  )
}

