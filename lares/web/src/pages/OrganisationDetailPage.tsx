import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { api } from '../lib/api'

export default function OrganisationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, error } = useQuery({
    queryKey: ['organisation', id],
    queryFn: () => api.getOrganisation(id!),
    enabled: !!id,
  })

  if (isLoading) return <div style={{ padding: 20, color: 'var(--text-dim)' }}>Loading…</div>
  if (error || !data) return <div style={{ padding: 20, color: 'var(--bad)' }}>Not found.</div>

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 20, maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 12, marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: 'var(--text-faint)', textTransform: 'uppercase' }}>{data.org_type}</div>
        <h1 style={{ fontSize: 20, margin: '4px 0' }}>{data.legal_name}</h1>
        <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-dim)' }}>
          <span>{data.hq_city ? `${data.hq_city}, ` : ''}{data.hq_country ?? 'HQ unknown'}</span>
          <span>{data.ownership_class}</span>
          {data.website && (
            <a href={data.website} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>
              {data.website}
            </a>
          )}
        </div>
      </div>

      {(data.direct_parent || data.ultimate_parent) && (
        <section style={sectionStyle}>
          <h2 style={h2}>Corporate structure</h2>
          <div style={{ fontSize: 12.5 }}>
            {data.direct_parent && (
              <div>
                Direct parent: <Link to={`/organisations/${data.direct_parent.id}`}>{data.direct_parent.legal_name}</Link>
              </div>
            )}
            {data.ultimate_parent && (
              <div>
                Ultimate parent: <Link to={`/organisations/${data.ultimate_parent.id}`}>{data.ultimate_parent.legal_name}</Link>
              </div>
            )}
          </div>
        </section>
      )}

      <section style={sectionStyle}>
        <h2 style={h2}>
          Infrastructure portfolio <span style={{ color: 'var(--text-dim)', fontWeight: 400 }}>({data.infrastructure_portfolio.length} across {data.countries_covered.join(', ') || '—'})</span>
        </h2>
        {data.infrastructure_portfolio.length === 0 ? (
          <p style={{ color: 'var(--text-faint)', fontSize: 12.5 }}>No infrastructure linked yet.</p>
        ) : (
          <table>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-faint)', fontSize: 11, textTransform: 'uppercase' }}>
                <th style={th}>Name</th>
                <th style={th}>Kind</th>
                <th style={th}>Category</th>
                <th style={th}>Country</th>
              </tr>
            </thead>
            <tbody>
              {data.infrastructure_portfolio.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={td}>
                    <Link to={`/infrastructure/${p.id}`}>{p.canonical_name}</Link>
                  </td>
                  <td style={td}>{p.kind}</td>
                  <td style={td}>{p.category}</td>
                  <td style={td}>{p.country ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {data.subsidiaries.length > 0 && (
        <section style={sectionStyle}>
          <h2 style={h2}>Subsidiaries</h2>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5 }}>
            {data.subsidiaries.map((s) => (
              <li key={s.id}>
                <Link to={`/organisations/${s.id}`}>{s.legal_name}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.roles.length > 0 && (
        <section style={sectionStyle}>
          <h2 style={h2}>Relevant roles</h2>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5 }}>
            {data.roles.map((r) => (
              <li key={r.id}>
                {r.role_category} {r.title_as_seen && `— ${r.title_as_seen}`} {r.is_filled ? '' : '(unfilled / unknown)'}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

const sectionStyle: React.CSSProperties = { marginBottom: 22 }
const h2: React.CSSProperties = { fontSize: 12.5, textTransform: 'uppercase', color: 'var(--text-dim)', letterSpacing: 0.4, marginBottom: 8 }
const th: React.CSSProperties = { padding: '6px 8px', fontWeight: 500 }
const td: React.CSSProperties = { padding: '6px 8px', fontSize: 12.5 }
