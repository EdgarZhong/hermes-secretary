import { describe, expect, it } from 'vitest'

import { compactNumber, formatEpochTimestamp } from './format'

describe('compactNumber', () => {
  it.each([
    [0, '0'],
    [999, '999'],
    [1000, '1k'],
    [1500, '1.5k'],
    [128_000, '128k'],
    // Promotion guard: a value that would round to "1000k" promotes to M.
    [999_949, '999.9k'],
    [999_999, '1M'],
    [1_000_000, '1M'],
    [1_500_000, '1.5M'],
    // `M` is the declared top rung (see format.ts): no `B`, so billions stay in M.
    [1_000_000_000, '1000M']
  ])('%d → %s', (value, expected) => {
    expect(compactNumber(value)).toBe(expected)
  })

  it('never emits a unit-boundary artifact like "1000k" or "1000"', () => {
    for (const value of [999.5, 999.9, 999_950, 999_999.4]) {
      expect(compactNumber(value)).not.toMatch(/^1000(\.\d)?k?$/)
    }
  })
})

describe('formatEpochTimestamp', () => {
  it('keeps epoch fractions, offset and the original instant', () => {
    expect(formatEpochTimestamp(1791756123.25)).toBe('2026-10-11T22:02:03.25Z')
    expect(formatEpochTimestamp(1791800714.1486568)).toBe('2026-10-12T10:25:14.1486568Z')
    expect(formatEpochTimestamp(-1.25)).toBe('1969-12-31T23:59:58.75Z')
    expect(formatEpochTimestamp(1e-7)).toBe('1970-01-01T00:00:00.0000001Z')
    expect(formatEpochTimestamp(Number.NaN)).toBe('unknown')
  })
})
