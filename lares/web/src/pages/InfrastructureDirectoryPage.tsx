import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { categoryColor } from '../lib/categoryColor'

export default function InfrastructureDirectoryPage() {
  const [country, setCountry] = useState('')
  const [category, setCategory] = useState('')
  const [q, setQ] = useState('')
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['infrastructures', country, category, q],
    queryFn: () => api.listInfrastructures({ country: country || undefined, category: category || undefined, q: q || undefined }),
  })

  return (
    <div style={{ padding: 16, height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          placeholder="Filter by name..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ padding: '5px 8px', fontSize: 12.5, background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--text)', width: 220 }}
        />
        <input
          placeholder="Country (ISO2)"
          value={country}
          onChange={(e) => setCountry(e.target.value.toUpperCase())}
          style={{ padding: '5px 8px', fontSize: 12.5, background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--text)', width: 120 }}
        />
        <input
          placeholder="Category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          style={{ padding: '5px 8px', fontSize: 12.5, background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--text)', width: 160 }}
        />
        <div style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-dim)', alignSelf: 'center' }}>
          {data ? `${data.total} results` : ''}
        </div>
      </div>

      {isLoading ? (
        <div style={{ color: 'var(--text-dim)' }}>Loading…</div>
      ) : (
        <table>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-faint)', fontSize: 11, textTransform: 'uppercase' }}>
              <th style={th}>Infrastructure</th>
              <th style={th}>Kind</th>
              <th style={th}>Category</th>
              <th style={th}>Country</th>
              <th style={th}>Operator</th>
              <th style={th}>Lares Fit</th>
              <th style={th}>State</th>
              <th style={th}>Verified</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((item) => (
              <tr
                key={item.id}
                onClick={() => navigate(`/infrastructure/${item.id}`)}
                style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--panel)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <td style={td}>
                  <span style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%', background: categoryColor(item.category), marginRight: 6 }} />
                  {item.canonical_name}
                </td>
                <td style={td}>{item.kind}</td>
                <td style={td}>{item.category}</td>
                <td style={td}>{item.country ?? '—'}</td>
                <td style={td}>{item.operator ?? <span style={{ color: 'var(--text-faint)' }}>unknown</span>}</td>
                <td style={td}>{item.lares_fit ?? '—'}</td>
                <td style={td}>{item.sales_readiness_state ?? '—'}</td>
                <td style={td}>{item.last_verified_at ?? '—'}</td>
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
