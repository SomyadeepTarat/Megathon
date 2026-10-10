// Standalone frontend preview. No network requests.
import { demo } from './demo';
export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }
export const api = demo;
