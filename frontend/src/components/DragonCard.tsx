import type { Dragon } from '../lib/api'
import { dragonImageUrl } from '../lib/dragonImage'
import './DragonCard.css'

type DragonCardProps = {
  dragon: Dragon
  variant?: 'cove' | 'geode'
  canRemove?: boolean
  onRemove?: () => void
  density?: 'full' | 'compact'
}

export function DragonCard({
  dragon,
  variant = 'cove',
  canRemove = false,
  onRemove,
  density = 'full',
}: DragonCardProps) {
  const classes = ['dragon-card', `dragon-card--${variant}`, density === 'compact' ? 'dragon-card--compact' : ''].join(
    ' ',
  )

  const hours =
    dragon.time_remaining >= 0 ? `${dragon.time_remaining}h left` : dragon.time_remaining === -2 ? 'Faded' : 'Stable'

  return (
    <article className={classes} aria-label={`Dragon ${dragon.dragon_code}`}>
      <header className="dragon-card__header">
        <span className="dragon-card__code">{dragon.dragon_code}</span>
        {dragon.is_sick && <span className="dragon-card__badge">Urgent</span>}
      </header>
      <a
        className="dragon-card__figure"
        href={`https://dragcave.net/view/${encodeURIComponent(dragon.dragon_code)}`}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Open ${dragon.dragon_code} on Dragon Cave (new tab)`}
      >
        <img
          className="dragon-card__sprite"
          src={dragonImageUrl(dragon.dragon_code)}
          alt=""
          width={100}
          height={120}
          loading="lazy"
          decoding="async"
          referrerPolicy="no-referrer-when-downgrade"
        />
      </a>
      {density === 'full' ? (
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
      ) : (
        <div className="dragon-card__tooltip" role="note">
          <div className="dragon-card__tooltip-row">
            <span className="dragon-card__label">Views</span>
            <span className="dragon-card__value">{dragon.views.toLocaleString()}</span>
          </div>
          <div className="dragon-card__tooltip-row">
            <span className="dragon-card__label">Unique</span>
            <span className="dragon-card__value">{dragon.unique_clicks.toLocaleString()}</span>
          </div>
          <div className="dragon-card__tooltip-row">
            <span className="dragon-card__label">Time</span>
            <span className="dragon-card__value">{hours}</span>
          </div>
        </div>
      )}
      {canRemove && onRemove && (
        <button
          type="button"
          className="dragon-card__remove"
          onClick={onRemove}
          aria-label={`Remove ${dragon.dragon_code} from the cove`}
          title="Remove"
        >
          Remove
        </button>
      )}
    </article>
  )
}

