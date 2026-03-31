import { describe, expect, it } from 'vitest'
import { dragonImageUrl } from './dragonImage'

describe('dragonImageUrl', () => {
  it('builds dragcave image URL', () => {
    expect(dragonImageUrl('Ab12x')).toBe('https://dragcave.net/image/Ab12x.gif')
  })

  it('encodes special characters in code', () => {
    expect(dragonImageUrl('a+b')).toContain(encodeURIComponent('a+b'))
  })
})
