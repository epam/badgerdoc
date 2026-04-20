import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { cn, getConfidenceColor, getGreeting, getStatusColor, formatTimeAgo } from './utils'

describe('cn (className merger)', () => {
  it('should merge class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('should handle conditional classes', () => {
    const includeBar = true
    const skipBar = false
    expect(cn('foo', skipBar && 'bar', 'baz')).toBe('foo baz')
    expect(cn('foo', includeBar && 'bar', 'baz')).toBe('foo bar baz')
  })

  it('should merge tailwind classes correctly', () => {
    expect(cn('p-4', 'p-2')).toBe('p-2')
    expect(cn('bg-red-500', 'bg-blue-500')).toBe('bg-blue-500')
  })

  it('should handle arrays', () => {
    expect(cn(['foo', 'bar'])).toBe('foo bar')
  })

  it('should handle objects', () => {
    expect(cn({ foo: true, bar: false })).toBe('foo')
  })
})

describe('getConfidenceColor', () => {
  it('should return high confidence colors for High', () => {
    const result = getConfidenceColor('High')
    expect(result.label).toBe('High')
    expect(result.text).toContain('mint')
  })

  it('should return medium confidence colors for Medium', () => {
    const result = getConfidenceColor('Medium')
    expect(result.label).toBe('Medium')
    expect(result.text).toContain('foreground')
  })

  it('should return low confidence colors for Low', () => {
    const result = getConfidenceColor('Low')
    expect(result.label).toBe('Low')
    expect(result.text).toContain('muted')
  })

  it('should return correct bg colors', () => {
    expect(getConfidenceColor('High').bg).toContain('mint')
    expect(getConfidenceColor('Medium').bg).toContain('foreground')
    expect(getConfidenceColor('Low').bg).toContain('muted')
  })
})

describe('getGreeting', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should return "Good morning" before noon', () => {
    vi.setSystemTime(new Date(2024, 0, 1, 9, 0, 0))
    expect(getGreeting()).toBe('Good morning')
  })

  it('should return "Good afternoon" between noon and 5pm', () => {
    vi.setSystemTime(new Date(2024, 0, 1, 14, 0, 0))
    expect(getGreeting()).toBe('Good afternoon')
  })

  it('should return "Good evening" after 5pm', () => {
    vi.setSystemTime(new Date(2024, 0, 1, 19, 0, 0))
    expect(getGreeting()).toBe('Good evening')
  })

  it('should handle edge cases', () => {
    vi.setSystemTime(new Date(2024, 0, 1, 12, 0, 0))
    expect(getGreeting()).toBe('Good afternoon')

    vi.setSystemTime(new Date(2024, 0, 1, 17, 0, 0))
    expect(getGreeting()).toBe('Good evening')

    vi.setSystemTime(new Date(2024, 0, 1, 0, 0, 0))
    expect(getGreeting()).toBe('Good morning')
  })
})

describe('getStatusColor', () => {
  it('should return correct colors for pending_review', () => {
    const result = getStatusColor('pending_review')
    expect(result.label).toBe('Pending Review')
    expect(result.action).toBe('Review')
  })

  it('should return correct colors for approved', () => {
    const result = getStatusColor('approved')
    expect(result.label).toBe('Approved')
    expect(result.action).toBe('View')
  })

  it('should return correct colors for declined', () => {
    const result = getStatusColor('declined')
    expect(result.label).toBe('Declined')
    expect(result.action).toBe('View')
  })

  it('should return correct colors for pending_extraction', () => {
    const result = getStatusColor('pending_extraction')
    expect(result.label).toBe('In Extraction')
    expect(result.action).toBe('Validate')
  })

  it('should return correct colors for extraction_complete', () => {
    const result = getStatusColor('extraction_complete')
    expect(result.label).toBe('Awaiting Approval')
    expect(result.action).toBe('Approve')
  })

  it('should return correct colors for final_approved', () => {
    const result = getStatusColor('final_approved')
    expect(result.label).toBe('Completed')
    expect(result.action).toBe('View')
  })

  it('should default to pending_review for unknown status', () => {
    const result = getStatusColor('unknown_status')
    expect(result.label).toBe('Pending Review')
  })
})

describe('formatTimeAgo', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2024, 5, 15, 12, 0, 0))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should return "Just now" for very recent times', () => {
    const now = new Date()
    expect(formatTimeAgo(now)).toBe('Just now')
  })

  it('should return minutes ago for recent times', () => {
    const fiveMinutesAgo = new Date(2024, 5, 15, 11, 55, 0)
    expect(formatTimeAgo(fiveMinutesAgo)).toBe('5m ago')
  })

  it('should return hours ago for same day', () => {
    const threeHoursAgo = new Date(2024, 5, 15, 9, 0, 0)
    expect(formatTimeAgo(threeHoursAgo)).toBe('3h ago')
  })

  it('should return days ago for recent days', () => {
    const twoDaysAgo = new Date(2024, 5, 13, 12, 0, 0)
    expect(formatTimeAgo(twoDaysAgo)).toBe('2d ago')
  })

  it('should return formatted date for older times', () => {
    const twoWeeksAgo = new Date(2024, 5, 1, 12, 0, 0)
    const result = formatTimeAgo(twoWeeksAgo)
    expect(result).toMatch(/\d{1,2}\/\d{1,2}\/\d{4}/)
  })

  it('should handle string dates', () => {
    const dateString = new Date(2024, 5, 15, 11, 30, 0).toISOString()
    expect(formatTimeAgo(dateString)).toBe('30m ago')
  })
})
