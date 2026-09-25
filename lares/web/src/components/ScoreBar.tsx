export default function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const v = value ?? 0
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11.5 }}>
      <div style={{ width: 140, color: 'var(--text-dim)', flexShrink: 0 }}>{label.replace(/_/g, ' ')}</div>
      <div style={{ flex: 1, height: 6, background: 'var(--panel-raised)', borderRadius: 2, overflow: 'hidden' }}>
        <div
          style={{
            width: `${v}%`,
            height: '100%',
            background: v >= 60 ? 'var(--good)' : v >= 30 ? 'var(--warn)' : 'var(--text-faint)',
          }}
        />
      </div>
      <div style={{ width: 24, textAlign: 'right', color: 'var(--text-dim)' }}>{value ?? '—'}</div>
    </div>
  )
}
