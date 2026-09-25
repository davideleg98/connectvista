const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8123'

async function request<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(API_BASE + path)
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== '') url.searchParams.set(k, String(v))
    }
  }
  const resp = await fetch(url.toString())
  if (!resp.ok) {
    if (resp.status === 404) throw new Error('not_found')
    throw new Error(`API error ${resp.status}`)
  }
  return resp.json() as Promise<T>
}

export interface InfrastructureSummary {
  id: string
  kind: 'asset' | 'cluster' | 'network'
  canonical_name: string
  category: string
  subcategory: string | null
  country: string | null
  status: string | null
  lon: number | null
  lat: number | null
  geometry_precision: string
  sensitivity_level: string
  operator: string | null
  operator_id: string | null
  owner: string | null
  lares_fit: number | null
  data_completeness_score: number | null
  sales_readiness_state: string | null
  last_verified_at: string | null
}

export interface OrgGraphNode {
  role: string
  organisation_id: string
  legal_name: string
  org_type: string
  hq_country: string | null
  website: string | null
}

export interface EvidenceRow {
  predicate: string
  object_literal: string | null
  confidence: number
  verification_state: string
  excerpt: string | null
  extraction_method: string
  source_publisher: string | null
  source_title: string | null
  source_url: string | null
  source_published_at: string | null
}

export interface RelevanceBreakdown {
  strategic_importance: number
  physical_complexity: number
  response_complexity: number
  autonomous_fit: number
  security_intensity: number
  buyer_accessibility: number
  contactability: number
  procurement_signal: number
  change_signal: number
  data_confidence: number
  lares_fit: number
}

export interface InfrastructureDetail extends InfrastructureSummary {
  operational_description: string | null
  organisation_graph: OrgGraphNode[]
  relationships: unknown[]
  related_infrastructure: { id: string; kind: string; canonical_name: string; country: string | null }[]
  evidence: EvidenceRow[]
  projects: unknown[]
  procurement: { id: string; title: string; published_at: string | null; security_relevance_category: string | null }[]
  signals: { id: string; signal_type: string; summary: string; event_date: string | null; confidence: number }[]
  relevance_breakdown: RelevanceBreakdown | null
}

export interface OrganisationSummary {
  id: string
  legal_name: string
  trading_names: string[] | null
  org_type: string
  hq_country: string | null
  hq_city: string | null
  website: string | null
  ownership_class: string
  lei: string | null
}

export interface OrganisationDetail extends OrganisationSummary {
  legal_form: string | null
  company_number: string | null
  jurisdiction: string | null
  revenue_eur_estimate: number | null
  employee_estimate: number | null
  last_verified_at: string | null
  direct_parent: OrganisationSummary | null
  ultimate_parent: OrganisationSummary | null
  subsidiaries: OrganisationSummary[]
  infrastructure_portfolio: { id: string; kind: string; canonical_name: string; country: string | null; category: string; lon: number | null; lat: number | null }[]
  countries_covered: string[]
  roles: { id: string; role_category: string; title_as_seen: string | null; is_filled: boolean }[]
}

export const api = {
  listInfrastructures: (params?: { country?: string; category?: string; q?: string; min_lares_fit?: number }) =>
    request<{ total: number; items: InfrastructureSummary[] }>('/api/infrastructures', params),
  getInfrastructure: (id: string) => request<InfrastructureDetail>(`/api/infrastructures/${id}`),
  listOrganisations: (params?: { country?: string; q?: string }) =>
    request<{ total: number; items: OrganisationSummary[] }>('/api/organisations', params),
  getOrganisation: (id: string) => request<OrganisationDetail>(`/api/organisations/${id}`),
  mapBbox: (params: { min_lon: number; min_lat: number; max_lon: number; max_lat: number; category?: string; country?: string }) =>
    request<{ count: number; features: InfrastructureSummary[] }>('/api/map/bbox', params as Record<string, string | number>),
  search: (q: string) =>
    request<{
      infrastructures: { id: string; kind: string; canonical_name: string; country: string | null }[]
      organisations: { id: string; legal_name: string; org_type: string; hq_country: string | null }[]
      procurement: { id: string; title: string }[]
      signals: { id: string; summary: string }[]
    }>('/api/search', { q }),
  coverage: () => request<{ matrix: Record<string, Record<string, { candidates: number; with_operator: number; outreach_ready: number }>> }>('/api/coverage'),
  sources: () => request<{ items: any[] }>('/api/sources'),
}
