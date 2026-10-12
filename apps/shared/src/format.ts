// THE compact-number formatter — every user-facing count/token figure goes
// through here. 999 → "999", 1000 → "1k", 1230 → "1.2k", 10000 → "10k",
// 1_500_000 → "1.5M". `M` is the top rung by design: token and cost figures
// this renders stay well under a billion, so 1e9 reads "1000M" rather than
// growing a `B` rung that no surface needs (and that would collide with the
// "bytes" reading in size labels). Do not hand-roll `/ 1000` display math elsewhere.
export function compactNumber(value: null | number | undefined): string {
  const num = Number(value ?? 0)

  if (!Number.isFinite(num) || num <= 0) {
    return '0'
  }

  const scaled = (v: number, suffix: string) => `${v.toFixed(1).replace(/\.0$/, '')}${suffix}`

  // Thresholds sit just under the unit boundary so rounding can't produce
  // "1000k" or "1000" — those promote to the next unit instead.
  if (num >= 999_950) {
    return scaled(num / 1_000_000, 'M')
  }

  if (num >= 999.5) {
    return scaled(num / 1_000, 'k')
  }

  return `${Math.round(num)}`
}

/** Render epoch seconds with explicit UTC, preserving the source Number's decimal precision. */
export function formatEpochTimestamp(epochSeconds: number): string {
  const date = new Date(Math.floor(epochSeconds) * 1000)

  if (!Number.isFinite(epochSeconds) || Number.isNaN(date.getTime())) {
    return 'unknown'
  }
  const [coefficient, exponentText = '0'] = Math.abs(epochSeconds).toString().split('e')
  const [integer, decimal = ''] = coefficient.split('.')
  const digits = integer + decimal
  const point = integer.length + Number(exponentText)
  const expanded = point < 0 ? '0'.repeat(-point) + digits : digits.slice(point)
  let fraction = (point < digits.length ? expanded : '').replace(/0+$/, '')

  if (epochSeconds < 0 && fraction) {
    fraction = (10n ** BigInt(fraction.length) - BigInt(fraction)).toString()
      .padStart(fraction.length, '0').replace(/0+$/, '')
  }

  const base = date.toISOString()

  return fraction ? base.replace('.000Z', `.${fraction}Z`) : base
}
