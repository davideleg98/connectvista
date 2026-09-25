import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function SourcesPage() {
  const { data, isLoading } = useQuery({ queryKey: ['sources'], queryFn: api.sources })

  if (isLoading || !data) return <div style={{ padding: 20, color: 'var(--text-dim)' }}>Loading…</div>

  return (
    <div style={{ padding: 20 }}>
      <h1 style={{ fontSize: 16, marginBottom: 4 }}>Source registry</h1>
      <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 16 }}>
        See lares/SOURCES.md and lares/DATA_GOVERNANCE.md. Provenance for every fact in this system traces back to
        one of these adapters.
      </p>
      <table>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-faint)', fontSize: 11, textTransform: 'uppercase' }}>
            <th style={th}>Source</th>
            <th style={th}>Tier</th>
            <th style={th}>Licence</th>
            <th style={th}>Cadence</th>
            <th style={th}>Enabled</th>
            <th style={th}>Last success</th>
            <th style={th}>Last failure</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((s: any) => (
            <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
              <td style={td}>{s.name}</td>
              <td style={td}>{s.tier}</td>
              <td style={td}>{s.licence_status}</td>
              <td style={td}>{s.update_cadence}</td>
              <td style={td}>{s.enabled ? 'yes' : 'no'}</td>
              <td style={td}>{s.last_successful_run_at ?? '—'}</td>
              <td style={td}>{s.last_failure_at ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const th: React.CSSProperties = { padding: '6px 8px', fontWeight: 500 }
const td: React.CSSProperties = { padding: '6px 8px', fontSize: 12.5 }
