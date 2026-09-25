import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { api } from '../lib/api'
import ScoreBar from '../components/ScoreBar'

export default function InfrastructureDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, error } = useQuery({
    queryKey: ['infrastructure', id],
    queryFn: () => api.getInfrastructure(id!),
    enabled: !!id,
  })

  if (isLoading) return <div style={{ padding: 20, color: 'var(--text-dim)' }}>Loading…</div>
  if (error || !data) return <div style={{ padding: 20, color: 'var(--bad)' }}>Not found.</div>

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 20, maxWidth: 1100, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 12, marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: 'var(--text-faint)', textTransform: 'uppercase' }}>
          {data.category} {data.subcategory ? `· ${data.subcategory}` : ''} · {data.kind}
        </div>
        <h1 style={{ fontSize: 20, margin: '4px 0' }}>{data.canonical_name}</h1>
        <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-dim)' }}>
          <span>{data.country ?? 'Country unknown'}</span>
          <span>Status: {data.status ?? 'unknown'}</span>
          <span>Sensitivity: {data.sensitivity_level}</span>
          <span>Geometry: {data.geometry_precision}</span>
          {data.last_verified_at && <span>Verified {data.last_verified_at}</span>}
        </div>
      </div>

      {/* Executive brief */}
      {data.operational_description && (
        <section style={sectionStyle}>
          <h2 style={h2}>What it is</h2>
          <p style={{ fontSize: 13, lineHeight: 1.6 }}>{data.operational_description}</p>
        </section>
      )}

      {/* Organisation graph */}
      <section style={sectionStyle}>
        <h2 style={h2}>Who controls it</h2>
        {data.organisation_graph.length === 0 ? (
          <p style={{ color: 'var(--text-faint)', fontSize: 12.5 }}>No operator/owner identified yet.</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {data.organisation_graph.map((n, i) => (
              <Link
                key={i}
                to={`/organisations/${n.organisation_id}`}
                style={{
                  display: 'block',
                  padding: '8px 12px',
                  background: 'var(--panel)',
                  border: '1px solid var(--border)',
                  borderRadius: 4,
                  textDecoration: 'none',
                  minWidth: 180,
                }}
              >
                <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--text-faint)' }}>{n.role.replace(/_/g, ' ')}</div>
                <div style={{ fontSize: 13, marginTop: 2 }}>{n.legal_name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{n.org_type} · {n.hq_country}</div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Lares relevance */}
      {data.relevance_breakdown && (
        <section style={sectionStyle}>
          <h2 style={h2}>
            Lares relevance <span style={{ color: 'var(--accent)', fontWeight: 600 }}>· {data.relevance_breakdown.lares_fit}/100</span>
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 24px', marginTop: 8 }}>
            {Object.entries(data.relevance_breakdown)
              .filter(([k]) => k !== 'lares_fit')
              .map(([k, v]) => (
                <ScoreBar key={k} label={k} value={v as number} />
              ))}
          </div>
        </section>
      )}

      {/* Signals */}
      <section style={sectionStyle}>
        <h2 style={h2}>Signals — why now</h2>
        {data.signals.length === 0 ? (
          <p style={{ color: 'var(--text-faint)', fontSize: 12.5 }}>No signals recorded yet.</p>
        ) : (
          data.signals.map((s) => (
            <div key={s.id} style={{ fontSize: 12.5, padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
              <strong>{s.signal_type.replace(/_/g, ' ')}</strong> — {s.summary}{' '}
              <span style={{ color: 'var(--text-faint)' }}>({s.event_date ?? 'undated'}, confidence {s.confidence})</span>
            </div>
          ))
        )}
      </section>

      {/* Procurement */}
      <section style={sectionStyle}>
        <h2 style={h2}>Procurement</h2>
        {data.procurement.length === 0 ? (
          <p style={{ color: 'var(--text-faint)', fontSize: 12.5 }}>No linked procurement notices yet.</p>
        ) : (
          data.procurement.map((p) => (
            <div key={p.id} style={{ fontSize: 12.5, padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
              {p.title} {p.security_relevance_category && <em>({p.security_relevance_category})</em>}
            </div>
          ))
        )}
      </section>

      {/* Related infrastructure */}
      <section style={sectionStyle}>
        <h2 style={h2}>Related infrastructure (same operator)</h2>
        {data.related_infrastructure.length === 0 ? (
          <p style={{ color: 'var(--text-faint)', fontSize: 12.5 }}>None found.</p>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5 }}>
            {data.related_infrastructure.map((r) => (
              <li key={r.id}>
                <Link to={`/infrastructure/${r.id}`}>{r.canonical_name}</Link> ({r.country})
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Evidence */}
      <section style={sectionStyle}>
        <h2 style={h2}>Evidence</h2>
        {data.evidence.length === 0 ? (
          <p style={{ color: 'var(--bad)', fontSize: 12.5 }}>No evidence recorded — this record should not be treated as verified.</p>
        ) : (
          data.evidence.map((e, i) => (
            <div key={i} style={{ fontSize: 12, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <div>
                <strong>{e.predicate}</strong> {e.object_literal && `— ${e.object_literal}`}{' '}
                <span style={{ color: 'var(--text-faint)' }}>
                  (confidence {e.confidence}, {e.verification_state})
                </span>
              </div>
              {e.excerpt && <div style={{ color: 'var(--text-dim)', marginTop: 2 }}>{e.excerpt}</div>}
              {e.source_url && (
                <div style={{ marginTop: 2 }}>
                  <a href={e.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>
                    {e.source_title || e.source_url}
                  </a>{' '}
                  <span style={{ color: 'var(--text-faint)' }}>— {e.source_publisher}</span>
                </div>
              )}
            </div>
          ))
        )}
      </section>
    </div>
  )
}

const sectionStyle: React.CSSProperties = { marginBottom: 22 }
const h2: React.CSSProperties = { fontSize: 12.5, textTransform: 'uppercase', color: 'var(--text-dim)', letterSpacing: 0.4, marginBottom: 8 }
