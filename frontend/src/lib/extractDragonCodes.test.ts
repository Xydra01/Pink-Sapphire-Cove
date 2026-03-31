import { describe, expect, it } from 'vitest'
import {
  capDragonCodesForRequest,
  extractDragonCodesFromPaste,
  MAX_DRAGON_CODES_PER_REQUEST,
} from './extractDragonCodes'

describe('extractDragonCodesFromPaste', () => {
  it('returns empty array for empty input', () => {
    expect(extractDragonCodesFromPaste('')).toEqual([])
    expect(extractDragonCodesFromPaste('   \n\t  ')).toEqual([])
  })

  it('extracts plain newline-separated codes', () => {
    expect(extractDragonCodesFromPaste('Ab12x\nCd34y')).toEqual(['Ab12x', 'Cd34y'])
  })

  it('dedupes case-insensitively preserving first casing', () => {
    expect(extractDragonCodesFromPaste('aaAA1\naaaa1')).toEqual(['aaAA1'])
  })

  it('extracts codes from dragcave.net view URLs', () => {
    const paste = 'check https://dragcave.net/view/zYx9w and also http://dragcave.net/lineage/aB3'
    expect(extractDragonCodesFromPaste(paste)).toEqual(['zYx9w', 'aB3'])
  })

  it('extracts from relative /view/ paths', () => {
    const paste = '<a href="/view/qwert">egg</a>'
    expect(extractDragonCodesFromPaste(paste)).toContain('qwert')
  })

  it('extracts standalone 4–5 char tokens from text with HTML stripped', () => {
    const paste = '<p>My codes: <b>xx99a</b> and yy88b</p>'
    expect(extractDragonCodesFromPaste(paste)).toEqual(expect.arrayContaining(['xx99a', 'yy88b']))
  })

  it('does not treat 6+ char tokens as a single code', () => {
    expect(extractDragonCodesFromPaste('password')).toEqual([])
  })

  it('allows 1–3 char codes only from URL paths (API allows 1–5)', () => {
    const paste = 'https://dragcave.net/view/x1'
    expect(extractDragonCodesFromPaste(paste)).toEqual(['x1'])
  })
})

describe('capDragonCodesForRequest', () => {
  it('truncates when over max', () => {
    const many = Array.from({ length: MAX_DRAGON_CODES_PER_REQUEST + 10 }, (_, i) => `a${i}`)
    const { codes, truncated } = capDragonCodesForRequest(many)
    expect(truncated).toBe(true)
    expect(codes).toHaveLength(MAX_DRAGON_CODES_PER_REQUEST)
  })
})
