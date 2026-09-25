import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

export default function OrganisationDirectoryPage() {
  const [q, setQ] = useState('')
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['organisations', q],
    queryFn: () => api.listOrganisations({ q: q || undefined }),
  })

  return (
    <div style={{ padding: 16, height: '100%', overflowY: 'auto' }}>
      <input
        placeholder="Filter by name..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
        style={{ padding: '5px 8px', fontSize: 12.5, background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--text)', width: 260, marginBottom: 12 }}
      />
      {isLoading ? (
        <div style={{ color: 'var(--text-dim)' }}>Loading…</div>
      ) : (
        <table>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-faint)', fontSize: 11, textTransform: 'uppercase' }}>
              <th style={th}>Organisation</th>
              <th style={th}>Type</th>
              <th style={th}>Country</th>
              <th style={th}>Ownership</th>
              <th style={th}>Website</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((o) => (
              <tr
                key={o.id}
                onClick={() => navigate(`/organisations/${o.id}`)}
                style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--panel)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <td style={td}>{o.legal_name}</td>
                <td style={td}>{o.org_type}</td>
                <td style={td}>{o.hq_country ?? '—'}</td>
                <td style={td}>{o.ownership_class}</td>
                <td style={td}>{o.website ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '6px 8px', fontWeight: 500 }
const td: React.CSSProperties = { padding: '6px 8px', fontSize: 12.5 }
