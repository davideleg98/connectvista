import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function CoveragePage() {
  const { data, isLoading } = useQuery({ queryKey: ['coverage'], queryFn: api.coverage })

  if (isLoading || !data) return <div style={{ padding: 20, color: 'var(--text-dim)' }}>Loading…</div>

  const countries = Object.keys(data.matrix).sort()
  const categories = Array.from(new Set(countries.flatMap((c) => Object.keys(data.matrix[c])))).sort()

  return (
    <div style={{ padding: 20 }}>
      <h1 style={{ fontSize: 16, marginBottom: 4 }}>Coverage matrix</h1>
      <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 16 }}>
        Candidates discovered / with operator identified / outreach-ready, by country × category. See spec §41 —
        this is how we know Europe is <em>not</em> "covered" just because one dataset produced many records.
      </p>
      <table>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-faint)', fontSize: 11, textTransform: 'uppercase' }}>
            <th style={th}>Country</th>
            {categories.map((c) => (
              <th key={c} style={th}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {countries.map((country) => (
            <tr key={country} style={{ borderBottom: '1px solid var(--border)' }}>
              <td style={{ ...td, fontWeight: 600 }}>{country}</td>
              {categories.map((cat) => {
                const cell = data.matrix[country][cat]
                return (
                  <td key={cat} style={td}>
                    {cell ? (
                      <span>
                        {cell.candidates} <span style={{ color: 'var(--text-faint)' }}>/ {cell.with_operator} / {cell.outreach_ready}</span>
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-faint)' }}>—</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const th: React.CSSProperties = { padding: '6px 8px', fontWeight: 500 }
const td: React.CSSProperties = { padding: '6px 8px', fontSize: 12.5 }
