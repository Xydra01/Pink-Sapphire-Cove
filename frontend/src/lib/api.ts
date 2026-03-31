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
  if (!res.ok) throw new Error(`Add dragons failed: ${res.status}`)
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

