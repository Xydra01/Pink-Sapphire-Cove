/** Dragon Cave egg/hatchling sprite URL used on scrolls and forums. */
export function dragonImageUrl(dragonCode: string): string {
  const code = encodeURIComponent(dragonCode.trim())
  return `https://dragcave.net/image/${code}.gif`
}
