type UnitType =
  | 'temperature'
  | 'length'
  | 'pressure'
  | 'mass'
  | 'density'
  | 'percentage'
  | 'thermal_expansion'
  | 'none'

// Unit groups by type
export const unitGroups: Record<UnitType, string[]> = {
  temperature: ['°C', '°F', 'K'],
  length: ['nm', 'μm', 'mm', 'cm', 'm', 'in', 'ft'],
  pressure: ['Pa', 'kPa', 'MPa', 'GPa', 'bar', 'psi', 'atm'],
  mass: ['mg', 'g', 'kg', 'oz', 'lb'],
  density: ['g/cm³', 'kg/m³', 'lb/ft³'],
  percentage: ['%', 'ppm', 'ppb'],
  thermal_expansion: ['×10⁻⁶/K', '×10⁻⁶/°C', '×10⁻⁷/K'],
  none: [],
}

// Detect unit type from unit string
export function detectUnitType(unit: string): UnitType {
  for (const [type, units] of Object.entries(unitGroups)) {
    if (units.includes(unit)) {
      return type as UnitType
    }
  }
  return 'none'
}
