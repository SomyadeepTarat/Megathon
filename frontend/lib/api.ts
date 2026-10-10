import { budgetPreview } from './placeholders.ts';
import type { Assessment, AssessmentRequest, PropertyRecord, PropertySummary, Scenario, Retrofit, Objective, AdvisorResult, Recommendation, RecommendationResponse, BaselineValuation } from './types.ts';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

async function request<T>(path: string, body?: unknown, scenarioResponse = false): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/backend${path}`, {
      method: body === undefined ? 'GET' : 'POST',
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
  health: () => request<{ status: string; readiness: Record<string, unknown> }>('/health'),
  properties: () => request<PropertySummary[]>('/properties'),
  property: (id: string) => request<PropertyRecord>(`/properties/${encodeURIComponent(id)}`),
  assessment: (id: string) => request<Assessment>(`/properties/${encodeURIComponent(id)}/assessment`),
  valuation: async (id: string, snapshot?: AssessmentRequest) => {
    if (snapshot) await request<PropertyRecord>('/properties', snapshot);
    return request<BaselineValuation>(`/properties/${encodeURIComponent(id)}/valuation`);
  },
  assess: (input: AssessmentRequest) => request<Assessment>('/assessments', input),
  simulate: (input: AssessmentRequest, retrofits: Retrofit[], budget_gbp: number | null, objective: Objective) => request<Scenario>('/scenarios/simulate', { ...input, retrofits, budget_gbp, objective }, true),
  recommendations: async (input: AssessmentRequest, budget_gbp: number | null, objective: Objective): Promise<{ items: Recommendation[]; warnings: string[] }> => {
    const result = await request<RecommendationResponse>('/retrofits/recommend', { ...input, budget_gbp, objective });
    const items = [...result.recommendations, ...result.other_options].map((option, index) => ({
      retrofit: option.retrofit, feasibility: option.feasibility, priority: index + 1,
      estimated_cost_gbp: option.scenario.installation_cost_gbp,
      energy: option.scenario.energy, carbon: option.scenario.carbon,
      reason: [option.feasibility.reason, option.scenario.reason].filter(Boolean).join(' '),
      assumptions: [...option.scenario.assumptions, ...option.scenario.warnings],
    }));
    return { items, warnings: [result.methodology, ...result.warnings] };
  },
  advisor: async (property_id: string, message: string, scenario?: { intent: string; retrofits: Retrofit[]; budget_gbp: number | null; objective: Objective }, snapshot?: AssessmentRequest) => {
    if (snapshot) {
      if (snapshot.property.property_id !== property_id) throw new ApiError(422, 'Advisor property differs from the selected home.');
      await request<PropertyRecord>('/properties', snapshot);
    }
    const result = await request<AdvisorResult>('/advisor/chat', { property_id, message, ...(scenario ? { scenario } : {}) });
    if (result.status === 'unavailable' && result.intent.intent === 'optimize_budget' && result.explanation.includes('Budget optimization is not integrated')) return budgetPreview(result.intent.budget_gbp);
    return result;
  },
};
