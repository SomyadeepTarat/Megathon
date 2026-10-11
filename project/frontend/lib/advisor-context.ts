import type { AdvisorResult } from './types.ts';

export function actionContext(messages: { result?: AdvisorResult }[]) {
  // A blocked scenario remains relevant; a newer baseline explanation replaces it.
  return [...messages].reverse().find((message) => message.result && message.result.intent.intent !== 'clarify')?.result?.intent;
}

export function needsPackageSelection(result: AdvisorResult) {
  return result.status === 'clarification_required' && result.clarification_kind === 'package';
}
