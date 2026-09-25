const COLORS: Record<string, string> = {
  energy: 'var(--cat-energy)',
  electricity_grid: 'var(--cat-energy)',
  maritime: 'var(--cat-maritime)',
  aviation: 'var(--cat-aviation)',
  digital: 'var(--cat-digital)',
  rail: 'var(--cat-rail)',
  rail_corridor: 'var(--cat-rail)',
  industrial: 'var(--cat-industrial)',
}

export function categoryColor(category: string): string {
  return COLORS[category] ?? '#6b7280'
}
