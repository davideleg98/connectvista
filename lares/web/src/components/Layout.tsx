import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useState } from 'react'

const NAV_ITEMS = [
  { to: '/map', label: 'Map' },
  { to: '/infrastructure', label: 'Infrastructure' },
  { to: '/organisations', label: 'Organisations' },
  { to: '/coverage', label: 'Coverage' },
  { to: '/sources', label: 'Sources' },
]

export default function Layout() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')

  function onSearch(e: React.FormEvent) {
    e.preventDefault()
    if (q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 24,
          padding: '0 16px',
          height: 44,
          borderBottom: '1px solid var(--border)',
          background: 'var(--panel)',
          flexShrink: 0,
        }}
      >
        <div style={{ fontWeight: 600, letterSpacing: 0.5, fontSize: 14 }}>
          Lares <span style={{ color: 'var(--text-dim)', fontWeight: 400 }}>· infrastructure intelligence</span>
        </div>
        <nav style={{ display: 'flex', gap: 4 }}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                padding: '6px 10px',
                fontSize: 12.5,
                color: isActive ? 'var(--text)' : 'var(--text-dim)',
                background: isActive ? 'var(--panel-raised)' : 'transparent',
                borderRadius: 3,
                textDecoration: 'none',
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <form onSubmit={onSearch} style={{ marginLeft: 'auto' }}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search infrastructure, organisations..."
            style={{
              width: 280,
              padding: '5px 8px',
              fontSize: 12.5,
              background: 'var(--bg)',
              border: '1px solid var(--border)',
              borderRadius: 3,
              color: 'var(--text)',
            }}
          />
        </form>
      </header>
      <div style={{ flex: 1, minHeight: 0 }}>
        <Outlet />
      </div>
    </div>
  )
}
