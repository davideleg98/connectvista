import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'

export default function SearchPage() {
  const [params] = useSearchParams()
  const q = params.get('q') ?? ''
  const { data, isLoading } = useQuery({
    queryKey: ['search', q],
    queryFn: () => api.search(q),
    enabled: q.length >= 2,
  })

  if (!q) return <div style={{ padding: 20, color: 'var(--text-dim)' }}>Enter a search query.</div>
  if (isLoading) return <div style={{ padding: 20, color: 'var(--text-dim)' }}>Searching…</div>

  return (
    <div style={{ padding: 20, maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontSize: 16, marginBottom: 16 }}>
        Results for <em>{q}</em>
      </h1>

      <Section title="Infrastructure">
        {data?.infrastructures.map((i) => (
          <div key={i.id}>
            <Link to={`/infrastructure/${i.id}`}>{i.canonical_name}</Link> <span style={{ color: 'var(--text-faint)' }}>({i.kind}, {i.country})</span>
          </div>
        ))}
      </Section>

      <Section title="Organisations">
        {data?.organisations.map((o) => (
          <div key={o.id}>
            <Link to={`/organisations/${o.id}`}>{o.legal_name}</Link> <span style={{ color: 'var(--text-faint)' }}>({o.org_type}, {o.hq_country})</span>
          </div>
        ))}
      </Section>

      <Section title="Procurement">
        {data?.procurement.map((p) => <div key={p.id}>{p.title}</div>)}
      </Section>

      <Section title="Signals">
        {data?.signals.map((s) => <div key={s.id}>{s.summary}</div>)}
      </Section>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const items = Array.isArray(children) ? children : [children]
  const hasContent = items.some(Boolean)
  return (
    <section style={{ marginBottom: 20 }}>
      <h2 style={{ fontSize: 12.5, textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: 6 }}>{title}</h2>
      {hasContent ? <div style={{ fontSize: 13, display: 'flex', flexDirection: 'column', gap: 4 }}>{children}</div> : <div style={{ color: 'var(--text-faint)', fontSize: 12.5 }}>No matches.</div>}
    </section>
  )
}
