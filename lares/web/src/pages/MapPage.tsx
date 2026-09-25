import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useNavigate } from 'react-router-dom'
import { api, type InfrastructureSummary } from '../lib/api'
import { categoryColor } from '../lib/categoryColor'

const CATEGORIES = ['', 'energy', 'electricity_grid', 'maritime', 'aviation', 'digital', 'rail_corridor', 'industrial']
const COUNTRIES = ['', 'IT', 'NL', 'DE', 'FR', 'GR']

export default function MapPage() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const navigate = useNavigate()

  const [category, setCategory] = useState('')
  const [country, setCountry] = useState('')
  const [features, setFeatures] = useState<InfrastructureSummary[]>([])

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          basemap: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
          },
        },
        layers: [{ id: 'basemap', type: 'raster', source: 'basemap' }],
      },
      center: [10, 50],
      zoom: 4,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    mapRef.current = map
    map.on('moveend', loadBbox)
    map.on('load', loadBbox)
    return () => {
      map.remove()
      mapRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function loadBbox() {
    const map = mapRef.current
    if (!map) return
    const bounds = map.getBounds()
    const result = await api.mapBbox({
      min_lon: bounds.getWest(),
      min_lat: bounds.getSouth(),
      max_lon: bounds.getEast(),
      max_lat: bounds.getNorth(),
      category: category || undefined,
      country: country || undefined,
    })
    setFeatures(result.features)
  }

  useEffect(() => {
    loadBbox()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, country])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    markersRef.current.forEach((m) => m.remove())
    markersRef.current = []
    for (const f of features) {
      if (f.lon == null || f.lat == null) continue
      const el = document.createElement('div')
      el.style.width = '10px'
      el.style.height = '10px'
      el.style.borderRadius = '50%'
      el.style.background = categoryColor(f.category)
      el.style.border = '1px solid rgba(255,255,255,0.6)'
      el.style.cursor = 'pointer'
      el.title = f.canonical_name
      el.onclick = () => navigate(`/infrastructure/${f.id}`)
      const marker = new maplibregl.Marker({ element: el }).setLngLat([f.lon, f.lat]).addTo(map)
      markersRef.current.push(marker)
    }
  }, [features, navigate])

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <aside
        style={{
          width: 220,
          borderRight: '1px solid var(--border)',
          background: 'var(--panel)',
          padding: 12,
          overflowY: 'auto',
          flexShrink: 0,
        }}
      >
        <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 8 }}>
          Filters
        </div>
        <label style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>Country</label>
        <select
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          style={selectStyle}
        >
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>
              {c || 'All countries'}
            </option>
          ))}
        </select>
        <label style={{ fontSize: 11.5, color: 'var(--text-dim)', marginTop: 10, display: 'block' }}>Category</label>
        <select value={category} onChange={(e) => setCategory(e.target.value)} style={selectStyle}>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c || 'All categories'}
            </option>
          ))}
        </select>

        <div style={{ marginTop: 16, fontSize: 11, textTransform: 'uppercase', color: 'var(--text-faint)' }}>
          {features.length} in view
        </div>
        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {features.map((f) => (
            <div
              key={f.id}
              onClick={() => navigate(`/infrastructure/${f.id}`)}
              style={{
                fontSize: 11.5,
                padding: '4px 6px',
                borderRadius: 3,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--panel-raised)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: categoryColor(f.category), flexShrink: 0 }} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.canonical_name}</span>
            </div>
          ))}
        </div>
      </aside>
      <div ref={mapContainer} style={{ flex: 1 }} />
    </div>
  )
}

const selectStyle: React.CSSProperties = {
  width: '100%',
  marginTop: 4,
  padding: '5px 6px',
  fontSize: 12,
  background: 'var(--bg)',
  border: '1px solid var(--border)',
  borderRadius: 3,
  color: 'var(--text)',
}
