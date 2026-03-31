/**
 * Dragon codes accepted by the FastAPI backend (see backend DRAGON_CODE_RE).
 */
export const DRAGON_CODE_PATTERN = /^[A-Za-z0-9]{1,5}$/

/** API accepts at most this many codes per request. */
export const MAX_DRAGON_CODES_PER_REQUEST = 200

/**
 * Pulls Dragon Cave–style codes out of pasted HTML, forum BBCode, full URLs, or plain lists.
 * Uses URL-focused patterns (1–5 alnum, matching the API) plus standalone 4–5 character tokens
 * to reduce false positives from longer words.
 */
export function extractDragonCodesFromPaste(raw: string): string[] {
  const ordered = new Map<string, string>()
  const text = raw ?? ''

  const add = (code: string) => {
    const trimmed = code.trim()
    if (!DRAGON_CODE_PATTERN.test(trimmed)) return
    const key = trimmed.toLowerCase()
    if (!ordered.has(key)) ordered.set(key, trimmed)
  }

  const dcNetPath = /dragcave\.net\/(?:view|lineage)\/([A-Za-z0-9]{1,5})(?![A-Za-z0-9])/gi
  for (const re of [dcNetPath]) {
    re.lastIndex = 0
    let m: RegExpExecArray | null
    while ((m = re.exec(text)) !== null) {
      add(m[1])
    }
  }

  const relViewPath = /\/(?:view|lineage)\/([A-Za-z0-9]{1,5})(?![A-Za-z0-9])/gi
  relViewPath.lastIndex = 0
  let m: RegExpExecArray | null
  while ((m = relViewPath.exec(text)) !== null) {
    add(m[1])
  }

  const deTagged = text.replace(/<[^>]+>/g, ' ')
  // Require at least one letter and one digit so words like "https" or "check" are not picked up.
  const standaloneMixed = /\b(?=[A-Za-z0-9]*[0-9])(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{4,5}\b/g
  standaloneMixed.lastIndex = 0
  while ((m = standaloneMixed.exec(deTagged)) !== null) {
    add(m[0])
  }

  return [...ordered.values()]
}

export function capDragonCodesForRequest(
  codes: string[],
  max = MAX_DRAGON_CODES_PER_REQUEST,
): { codes: string[]; truncated: boolean } {
  if (codes.length <= max) return { codes, truncated: false }
  return { codes: codes.slice(0, max), truncated: true }
}
