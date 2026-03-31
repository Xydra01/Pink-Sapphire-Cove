import { useMemo, useState } from 'react'
import { useAddDragons } from '../hooks/useAddDragons'
import {
  capDragonCodesForRequest,
  extractDragonCodesFromPaste,
  MAX_DRAGON_CODES_PER_REQUEST,
} from '../lib/extractDragonCodes'
import './BatchDropOff.css'

export function BatchDropOff() {
  const [paste, setPaste] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)
  const [truncationNote, setTruncationNote] = useState<string | null>(null)

  const extracted = useMemo(() => extractDragonCodesFromPaste(paste), [paste])
  const capped = useMemo(() => capDragonCodesForRequest(extracted), [extracted])

  const mutation = useAddDragons()

  const handleDropOff = () => {
    setLocalError(null)
    setTruncationNote(null)

    if (capped.codes.length === 0) {
      setLocalError('No dragon codes found. Paste links, HTML, or a list of codes (4–5 characters with letters and numbers).')
      return
    }

    if (capped.truncated) {
      setTruncationNote(
        `Only the first ${MAX_DRAGON_CODES_PER_REQUEST} codes are sent per batch (API limit).`,
      )
    }

    mutation.mutate(capped.codes)
  }

  return (
    <section className="batch-drop-off" aria-labelledby="batch-drop-off-heading">
      <h2 id="batch-drop-off-heading" className="batch-drop-off__title">
        <span>Drop off</span>
      </h2>
      <p className="batch-drop-off__hint">
        Paste anything from Dragon Cave—forum BBCode, HTML signatures, or plain links. We scan for{' '}
        <code>dragcave.net/view/…</code> paths and mixed letter+number codes (4–5 characters), then send them to the
        cove.
      </p>
      <div className="batch-drop-off__field">
        <label htmlFor="batch-paste" className="batch-drop-off__label">
          Paste your eggs &amp; hatchlings
        </label>
        <textarea
          id="batch-paste"
          className="batch-drop-off__textarea"
          value={paste}
          onChange={(e) => {
            setPaste(e.target.value)
            setLocalError(null)
            mutation.reset()
          }}
          placeholder="Paste HTML, links, or codes here…"
          spellCheck={false}
          autoComplete="off"
        />
      </div>
      <div className="batch-drop-off__meta">
        <span className="batch-drop-off__count">
          {capped.codes.length === 0
            ? 'No codes detected yet'
            : `${capped.codes.length} code${capped.codes.length === 1 ? '' : 's'} ready to drop off`}
        </span>
        <button
          type="button"
          className="batch-drop-off__submit"
          onClick={handleDropOff}
          disabled={mutation.isPending || capped.codes.length === 0}
        >
          {mutation.isPending ? 'Dropping off…' : 'Drop off'}
        </button>
      </div>
      {localError && (
        <p className="batch-drop-off__message batch-drop-off__message--error" role="alert">
          {localError}
        </p>
      )}
      {truncationNote && (
        <p className="batch-drop-off__message batch-drop-off__message--warn" role="status">
          {truncationNote}
        </p>
      )}
      {mutation.isError && (
        <p className="batch-drop-off__message batch-drop-off__message--error" role="alert">
          {mutation.error.message}
        </p>
      )}
      {mutation.isSuccess && mutation.data && (
        <p className="batch-drop-off__message batch-drop-off__message--success" role="status">
          Session updated. Added {mutation.data.dragons.length} dragon
          {mutation.data.dragons.length === 1 ? '' : 's'}
          {mutation.data.errors.length > 0
            ? `; ${mutation.data.errors.length} could not be added (see API errors).`
            : '.'}
        </p>
      )}
    </section>
  )
}
