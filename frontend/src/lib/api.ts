export type Dragon = {
  dragon_code: string
  views: number
  unique_clicks: number
  time_remaining: number
  is_sick: boolean
  can_remove: boolean
}

function messageFromFastApiBody(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object' || !('detail' in body)) return fallback
  const detail = (body as { detail: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const parts = detail
      .map((d) => {
        if (d && typeof d === 'object' && 'msg' in d && typeof (d as { msg: unknown }).msg === 'string') {
          return (d as { msg: string }).msg
        }
        return null
      })
      .filter(Boolean) as string[]
    if (parts.length) return parts.join('; ')
  }
  return fallback
}

async function errorMessageFromResponse(res: Response, fallback: string): Promise<string> {
  try {
    const body: unknown = await res.json()
    return messageFromFastApiBody(body, fallback)
  } catch {
    return fallback
  }
}

export async function fetchCove(): Promise<Dragon[]> {
  const sessionToken = typeof window !== 'undefined' ? window.localStorage.getItem('gem-cove-session-token') : null
  const res = await fetch('/api/dragons/cove', {
    headers: sessionToken ? { 'X-Session-Token': sessionToken } : undefined,
  })
  if (!res.ok) throw new Error(`Cove request failed: ${res.status}`)
  return (await res.json()) as Dragon[]
}

export async function fetchGeode(): Promise<Dragon[]> {
  const sessionToken = typeof window !== 'undefined' ? window.localStorage.getItem('gem-cove-session-token') : null
  const res = await fetch('/api/dragons/geode', {
    headers: sessionToken ? { 'X-Session-Token': sessionToken } : undefined,
  })
  if (!res.ok) throw new Error(`Geode request failed: ${res.status}`)
  return (await res.json()) as Dragon[]
}

export type AddDragonsResult = {
  session_token: string
  dragons: Dragon[]
  errors: { dragon_code: string; error: string }[]
}

export async function addDragons(codes: string[]): Promise<AddDragonsResult> {
  const res = await fetch('/api/dragons/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dragon_codes: codes }),
  })
  if (!res.ok) {
    throw new Error(await errorMessageFromResponse(res, `Add dragons failed: ${res.status}`))
  }
  return (await res.json()) as AddDragonsResult
}

export type ScrollDragonPreview = {
  dragon_code: string
  name: string
  accept_aid: boolean
}

export type ScrollPreviewResponse = {
  username: string
  dragons: ScrollDragonPreview[]
}

export async function previewScroll(input: string): Promise<ScrollPreviewResponse> {
  const res = await fetch('/api/dragons/scroll-preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input }),
  })
  if (!res.ok) {
    throw new Error(await errorMessageFromResponse(res, `Scroll preview failed: ${res.status}`))
  }
  return (await res.json()) as ScrollPreviewResponse
}

export async function removeDragons(sessionToken: string, codes?: string[]): Promise<{ removed: string[] }> {
  const res = await fetch('/api/dragons/remove', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_token: sessionToken, dragon_codes: codes ?? null }),
  })
  if (!res.ok) throw new Error(`Remove dragons failed: ${res.status}`)
  return (await res.json()) as { removed: string[] }
}

