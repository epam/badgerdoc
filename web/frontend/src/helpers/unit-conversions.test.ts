import { describe, it, expect } from 'vitest'
import { detectUnitType, unitGroups } from './unit-conversions'

describe('detectUnitType', () => {
  it('should detect temperature units', () => {
    expect(detectUnitType('°C')).toBe('temperature')
    expect(detectUnitType('°F')).toBe('temperature')
    expect(detectUnitType('K')).toBe('temperature')
  })

  it('should detect length units', () => {
    expect(detectUnitType('mm')).toBe('length')
    expect(detectUnitType('cm')).toBe('length')
    expect(detectUnitType('m')).toBe('length')
    expect(detectUnitType('in')).toBe('length')
    expect(detectUnitType('ft')).toBe('length')
    expect(detectUnitType('μm')).toBe('length')
    expect(detectUnitType('nm')).toBe('length')
  })

  it('should detect pressure units', () => {
    expect(detectUnitType('Pa')).toBe('pressure')
    expect(detectUnitType('kPa')).toBe('pressure')
    expect(detectUnitType('MPa')).toBe('pressure')
    expect(detectUnitType('GPa')).toBe('pressure')
    expect(detectUnitType('bar')).toBe('pressure')
    expect(detectUnitType('psi')).toBe('pressure')
    expect(detectUnitType('atm')).toBe('pressure')
  })

  it('should detect mass units', () => {
    expect(detectUnitType('g')).toBe('mass')
    expect(detectUnitType('kg')).toBe('mass')
    expect(detectUnitType('mg')).toBe('mass')
    expect(detectUnitType('lb')).toBe('mass')
    expect(detectUnitType('oz')).toBe('mass')
  })

  it('should detect density units', () => {
    expect(detectUnitType('g/cm³')).toBe('density')
    expect(detectUnitType('kg/m³')).toBe('density')
    expect(detectUnitType('lb/ft³')).toBe('density')
  })

  it('should detect percentage units', () => {
    expect(detectUnitType('%')).toBe('percentage')
    expect(detectUnitType('ppm')).toBe('percentage')
    expect(detectUnitType('ppb')).toBe('percentage')
  })

  it('should detect thermal expansion units', () => {
    expect(detectUnitType('×10⁻⁶/K')).toBe('thermal_expansion')
    expect(detectUnitType('×10⁻⁶/°C')).toBe('thermal_expansion')
    expect(detectUnitType('×10⁻⁷/K')).toBe('thermal_expansion')
  })

  it('should return none for unknown units', () => {
    expect(detectUnitType('unknown')).toBe('none')
    expect(detectUnitType('')).toBe('none')
  })
})

describe('unitGroups', () => {
  it('should have all expected unit types', () => {
    expect(Object.keys(unitGroups)).toEqual([
      'temperature',
      'length',
      'pressure',
      'mass',
      'density',
      'percentage',
      'thermal_expansion',
      'none',
    ])
  })

  it('should have none as empty array', () => {
    expect(unitGroups.none).toEqual([])
  })
})
