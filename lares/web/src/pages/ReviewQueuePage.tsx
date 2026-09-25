import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function ReviewQueuePage() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['review-queue'], queryFn: () => api.reviewQueue('pending') })

  async function act(id: string, action: 'approve' | 'reject') {
    if (action === 'approve') await api.approveReview(id)
    else await api.rejectReview(id)
    queryClient.invalidateQueries({ queryKey: ['review-queue'] })
  }

  if (isLoading || !data) return <div style={{ padding: 20, color: 'var(--text-dim)' }}>Loading…</div>

  return (
    <div style={{ padding: 20 }}>
      <h1 style={{ fontSize: 16, marginBottom: 4 }}>Review queue</h1>
      <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 16 }}>
        Ambiguous entity-resolution matches — never silently merged, never silently dropped. See spec §14 /
        lares/ONTOLOGY.md. Approving merges the candidate into the matched record; rejecting confirms they're
        genuinely different and leaves both as-is.
      </p>
      {data.items.length === 0 ? (
        <div style={{ fontSize: 12.5, color: 'var(--text-dim)' }}>No pending matches awaiting review.</div>
      ) : (
        <table>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-faint)', fontSize: 11, textTransform: 'uppercase' }}>
              <th style={th}>Type</th>
              <th style={th}>Candidate</th>
              <th style={th}>Possible match</th>
              <th style={th}>Score</th>
              <th style={th}>Method</th>
              <th style={th}></th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((r) => (
              <tr key={r.id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={td}>{r.entity_type}</td>
                <td style={td}>{r.candidate_name ?? r.candidate_entity_id}</td>
                <td style={td}>{r.matched_name ?? r.matched_entity_id}</td>
                <td style={td}>{r.match_score}</td>
                <td style={td}>{r.match_signals?.method ?? '—'}</td>
                <td style={{ ...td, display: 'flex', gap: 6 }}>
                  <button onClick={() => act(r.id, 'approve')} style={btn}>
                    Approve merge
                  </button>
                  <button onClick={() => act(r.id, 'reject')} style={btn}>
                    Reject — different entities
                  </button>
                </td>
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
const btn: React.CSSProperties = {
  padding: '3px 8px',
  fontSize: 11.5,
  background: 'var(--panel-raised)',
  border: '1px solid var(--border)',
  borderRadius: 3,
  color: 'var(--text)',
  cursor: 'pointer',
}
