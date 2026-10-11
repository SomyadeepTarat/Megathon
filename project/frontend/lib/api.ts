import type { Assessment, AssessmentRequest, PropertyRecord, PropertySummary, Scenario, Retrofit, Objective, AdvisorResult, Recommendation, RecommendationResponse, BaselineValuation, OptimizationResult, PortfolioRow } from './types.ts';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

async function request<T>(path: string, body?: unknown, scenarioResponse = false, method?: 'PUT'): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/backend${path}`, {
      method: method || (body === undefined ? 'GET' : 'POST'),
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: 'no-store',
    });
  } catch {
    throw new ApiError(0, 'Cannot reach the assessment service. Check that the backend is running.');
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (scenarioResponse && [409, 503].includes(response.status) && data?.scenario_id && data?.baseline_assessment && ['rejected', 'unavailable'].includes(data.status)) return data as T;
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item: { loc?: (string | number)[]; msg?: string }) => `${item.loc?.filter((part) => part !== 'body').join('.') || 'Input'}: ${item.msg || 'Invalid value'}`).join('; ')
      : typeof detail === 'string' ? detail : data?.reason || 'The assessment service could not complete this request.';
    throw new ApiError(response.status, message);
  }
  if (data === null) throw new ApiError(response.status, 'The assessment service returned an invalid response.');
  return data as T;
}

export const api = {
  memory: (id: string) => request<import('./types').CustomerMemory>(`/advisor/memory/${encodeURIComponent(id)}`),
  updateMemory: (id: string, update: { revision: number; preferences?: import('./types').CustomerMemory['preferences']; completed_retrofits?: Retrofit[]; feedback?: { retrofits: Retrofit[]; response: 'accepted' | 'rejected' | 'deferred' }; reset?: boolean }) => request<import('./types').CustomerMemory>(`/advisor/memory/${encodeURIComponent(id)}`, update, false, 'PUT'),
  register: (input: AssessmentRequest) => request<PropertyRecord>('/properties', input),
  health: () => request<{ status: string; readiness: Record<string, unknown> }>('/health'),
  propertyRanking: () => request<PortfolioRow[]>('/properties/ranking'),
  portfolio: () => request<PortfolioRow[]>('/portfolio/rank'),
  properties: () => request<PropertySummary[]>('/properties'),
  property: (id: string) => request<PropertyRecord>(`/properties/${encodeURIComponent(id)}`),
  assessment: (id: string) => request<Assessment>(`/properties/${encodeURIComponent(id)}/assessment`),
  valuation: async (id: string, snapshot?: AssessmentRequest) => {
    if (snapshot) await request<PropertyRecord>('/properties', snapshot);
    return request<BaselineValuation>(`/properties/${encodeURIComponent(id)}/valuation`);
  },
  assessFull: async (input: AssessmentRequest): Promise<Assessment> => { const result = await request<{ assessment: Assessment; baseline_carbon: Assessment['baseline_carbon'] }>('/assessments/full', input); return { ...result.assessment, baseline_carbon: result.baseline_carbon }; },
  assess: (input: AssessmentRequest) => request<Assessment>('/assessments', input),
  simulate: (input: AssessmentRequest, retrofits: Retrofit[], budget_gbp: number | null, objective: Objective) => request<Scenario>('/scenarios/simulate', { ...input, retrofits, budget_gbp, objective }, true),
  optimize: (input: AssessmentRequest, budget_gbp: number | null, objective: Objective) => request<OptimizationResult>('/retrofits/optimize', { ...input, budget_gbp, objective }),
  storedRecommendations: (propertyId: string, scenarioId?: string) => request<RecommendationResponse>(`/properties/${encodeURIComponent(propertyId)}/recommendations${scenarioId ? `?scenario_id=${encodeURIComponent(scenarioId)}` : ''}`),
  recommendations: async (input: AssessmentRequest, budget_gbp: number | null, objective: Objective, scenario_id?: string): Promise<{ items: Recommendation[]; warnings: string[] }> => {
    const saved = await request<RecommendationResponse>('/retrofits/recommend', { ...input, budget_gbp, objective, ...(scenario_id ? { scenario_id } : {}) });
    if (!saved.scenario_id) throw new ApiError(500, 'The service did not return a saved recommendation scenario.');
    const result = await api.storedRecommendations(input.property.property_id, saved.scenario_id);
    if (result.property_id !== input.property.property_id || result.scenario_id !== saved.scenario_id) throw new ApiError(500, 'Stored recommendations differ from the requested property or scenario.');
    const items = [...result.recommendations.map((option) => ({ ...option, recommended: true })), ...result.other_options.map((option) => ({ ...option, recommended: false }))].map((option) => ({
      retrofit: option.retrofit, feasibility: option.feasibility, priority: option.priority ?? null, recommended: option.recommended,
      suitability: option.suitability, suitability_reason: option.suitability_reason,
      annual_bill_savings_gbp: option.scenario.annual_bill_savings_gbp, simple_payback_years: option.scenario.simple_payback_years,
      estimated_cost_gbp: option.scenario.installation_cost_gbp,
      energy: option.scenario.energy, carbon: option.scenario.carbon,
      reason: [...new Set([option.feasibility.reason, option.scenario.reason, option.ranking_reason].filter(Boolean))].join(' '),
      assumptions: [...new Set([...option.scenario.assumptions, ...option.scenario.warnings])],
    }));
    return { items, warnings: [result.methodology, ...result.warnings,
      ...(result.installation_order?.length ? [`Suggested installation sequence: ${result.installation_order.map((id) => id.replaceAll('_', ' ')).join(' → ')}. Benefit rank is separate from installation order.`] : [])] };
  },
  advisorStream: async (property_id: string, message: string,
    onProgress: (message: string) => void, scenario?: AdvisorResult['intent'],
    snapshot?: AssessmentRequest, context?: AdvisorResult['intent']) => {
    if (snapshot) {
      if (snapshot.property.property_id !== property_id) throw new ApiError(422, 'Advisor property differs from the selected home.');
      await request<PropertyRecord>('/properties', snapshot);
    }
    const response = await fetch('/api/backend/advisor/chat/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ property_id, message, scenario, context }), cache: 'no-store',
    });
    if (!response.ok || !response.body) throw new ApiError(response.status, 'Cannot start the advisor. Check that the backend is running.');
    const reader = response.body.getReader();
    const decoder = new TextDecoder(); let buffer = '';
    try {
      while (true) {
        const chunk = await reader.read();
        buffer += decoder.decode(chunk.value, { stream: !chunk.done });
        let boundary: number;
        while ((boundary = buffer.indexOf('\n\n')) >= 0) {
          const block = buffer.slice(0, boundary); buffer = buffer.slice(boundary + 2);
          const event = block.split('\n').find((line) => line.startsWith('event: '))?.slice(7);
          const raw = block.split('\n').filter((line) => line.startsWith('data: ')).map((line) => line.slice(6)).join('\n');
          if (!raw) continue;
          const data = JSON.parse(raw);
          if (event === 'progress') onProgress(data.message);
          if (event === 'error') throw new ApiError(503, data.message);
          if (event === 'result') return data as AdvisorResult;
        }
        if (chunk.done) throw new ApiError(503, 'The advisor connection ended before an answer was ready. Please retry.');
      }
    } finally { await reader.cancel(); reader.releaseLock(); }
  },
  advisor: async (property_id: string, message: string, scenario?: { intent: string; retrofits: Retrofit[]; budget_gbp: number | null; objective: Objective }, snapshot?: AssessmentRequest) => {
    if (snapshot) {
      if (snapshot.property.property_id !== property_id) throw new ApiError(422, 'Advisor property differs from the selected home.');
      await request<PropertyRecord>('/properties', snapshot);
    }
    const result = await request<AdvisorResult>('/advisor/chat', { property_id, message, ...(scenario ? { scenario } : {}) });
    return result;
  },
};
