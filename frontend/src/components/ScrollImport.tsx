import { useMutation } from '@tanstack/react-query'
import { useCallback, useEffect, useId, useState } from 'react'
import { useAddDragons } from '../hooks/useAddDragons'
import { previewScroll } from '../lib/api'
import type { ScrollDragonPreview } from '../lib/api'
import { capDragonCodesForRequest } from '../lib/extractDragonCodes'
import { dragonImageUrl } from '../lib/dragonImage'
import './ScrollImport.css'

export function ScrollImport() {
  const inputId = useId()
  const [input, setInput] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const previewMutation = useMutation({
    mutationFn: previewScroll,
    onSuccess: (data) => {
      const addable = data.dragons.filter((d) => d.can_add).map((d) => d.dragon_code)
      setSelected(new Set(addable))
      setModalOpen(true)
    },
  })

  const addMutation = useAddDragons()

  const closeModal = useCallback(() => {
    setModalOpen(false)
    previewMutation.reset()
  }, [previewMutation])

  useEffect(() => {
    if (!modalOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeModal()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [modalOpen, closeModal])

  const data = previewMutation.data

  const toggleCode = (code: string, canAdd: boolean) => {
    if (!canAdd) return
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(code)) next.delete(code)
      else next.add(code)
      return next
    })
  }

  const selectAllAddable = () => {
    if (!data) return
    setSelected(new Set(data.dragons.filter((d) => d.can_add).map((d) => d.dragon_code)))
  }

  const clearSelection = () => setSelected(new Set())

  const addSelected = () => {
    const codes = Array.from(selected)
    if (codes.length === 0) return
    const { codes: capped } = capDragonCodesForRequest(codes)
    addMutation.mutate(capped, {
      onSuccess: () => {
        closeModal()
        setInput('')
      },
    })
  }

  const addAllAddable = () => {
    if (!data) return
    const codes = data.dragons.filter((d) => d.can_add).map((d) => d.dragon_code)
    const { codes: capped } = capDragonCodesForRequest(codes)
    addMutation.mutate(capped, {
      onSuccess: () => {
        closeModal()
        setInput('')
      },
    })
  }

  return (
    <section className="scroll-import" aria-labelledby="scroll-import-heading">
      <h2 id="scroll-import-heading" className="scroll-import__title">
        <span>From your scroll</span>
      </h2>
      <p className="scroll-import__hint">
        Paste your public scroll link (<code>dragcave.net/user/…</code>) or your Dragon Cave username. We load eggs and
        hatchlings only (via Dragon Cave&apos;s <code>user_young</code> API). You can add every dragon that has{' '}
        <strong>Accept aid</strong> turned on, or pick specific ones in the chooser.
      </p>
      <div className="scroll-import__row">
        <div className="scroll-import__field">
          <label htmlFor={inputId} className="scroll-import__label">
            Scroll URL or username
          </label>
          <input
            id={inputId}
            className="scroll-import__input"
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              previewMutation.reset()
            }}
            placeholder="https://dragcave.net/user/YourName or YourName"
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <button
          type="button"
          className="scroll-import__load"
          disabled={previewMutation.isPending || !input.trim()}
          onClick={() => previewMutation.mutate(input.trim())}
        >
          {previewMutation.isPending ? 'Loading…' : 'Load scroll'}
        </button>
      </div>
      {previewMutation.isError && (
        <p className="scroll-import__error" role="alert">
          {previewMutation.error.message}
        </p>
      )}

      {modalOpen && data && (
        <div
          className="scroll-import__backdrop"
          role="presentation"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) closeModal()
          }}
        >
          <div
            className="scroll-import__dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="scroll-dialog-title"
          >
            <div className="scroll-import__dialog-head">
              <div>
                <h3 id="scroll-dialog-title" className="scroll-import__dialog-title">
                  Choose dragons
                </h3>
                <p className="scroll-import__dialog-sub">
                  {data.username} — {data.dragons.length} growing on scroll
                </p>
              </div>
              <button type="button" className="scroll-import__close" onClick={closeModal}>
                Close
              </button>
            </div>
            <div className="scroll-import__list">
              {data.dragons.map((d: ScrollDragonPreview) => (
                <label
                  key={d.dragon_code}
                  className={`scroll-import__item${d.can_add ? '' : ' scroll-import__item--blocked'}`}
                >
                  <input
                    type="checkbox"
                    checked={selected.has(d.dragon_code)}
                    disabled={!d.can_add}
                    onChange={() => toggleCode(d.dragon_code, d.can_add)}
                  />
                  <img src={dragonImageUrl(d.dragon_code)} alt="" width={56} height={67} loading="lazy" />
                  <div className="scroll-import__item-main">
                    <span className="scroll-import__item-code">{d.dragon_code}</span>
                    {d.name ? <span className="scroll-import__item-name">{d.name}</span> : null}
                    {!d.can_add ? (
                      <span className="scroll-import__item-note">Accept aid is off — cannot add from hatchery</span>
                    ) : null}
                  </div>
                </label>
              ))}
            </div>
            {data.dragons.length === 0 ? (
              <p className="scroll-import__dialog-sub">No eggs or hatchlings on this scroll right now.</p>
            ) : null}
            <div className="scroll-import__actions">
              <button type="button" className="scroll-import__btn" onClick={selectAllAddable}>
                Select all (aid on)
              </button>
              <button type="button" className="scroll-import__btn" onClick={clearSelection}>
                Clear
              </button>
              <button type="button" className="scroll-import__btn" onClick={addAllAddable} disabled={addMutation.isPending}>
                Add all with aid on
              </button>
              <button
                type="button"
                className="scroll-import__btn scroll-import__btn--primary"
                onClick={addSelected}
                disabled={addMutation.isPending || selected.size === 0}
              >
                {addMutation.isPending ? 'Adding…' : `Add selected (${selected.size})`}
              </button>
            </div>
            {addMutation.isError ? (
              <p className="scroll-import__error" role="alert">
                {addMutation.error.message}
              </p>
            ) : null}
          </div>
        </div>
      )}
    </section>
  )
}
