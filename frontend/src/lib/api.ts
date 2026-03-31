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

