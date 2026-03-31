export type Dragon = {
  dragon_code: string
  views: number
  unique_clicks: number
  time_remaining: number
  is_sick: boolean
}

export async function fetchCove(): Promise<Dragon[]> {
  const res = await fetch('/api/dragons/cove')
  if (!res.ok) throw new Error(`Cove request failed: ${res.status}`)
  return (await res.json()) as Dragon[]
}

export async function fetchGeode(): Promise<Dragon[]> {
  const res = await fetch('/api/dragons/geode')
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
    let message = `Add dragons failed: ${res.status}`
    try {
      const body: unknown = await res.json()
      if (body && typeof body === 'object' && 'detail' in body) {
        const detail = (body as { detail: unknown }).detail
        if (typeof detail === 'string') message = detail
        else if (Array.isArray(detail)) {
          const parts = detail
            .map((d) => {
              if (d && typeof d === 'object' && 'msg' in d && typeof (d as { msg: unknown }).msg === 'string') {
                return (d as { msg: string }).msg
              }
              return null
            })
            .filter(Boolean)
          if (parts.length) message = parts.join('; ')
        }
      }
    } catch {
      /* ignore JSON parse errors */
    }
    throw new Error(message)
  }
  return (await res.json()) as AddDragonsResult
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

