import { env } from '$env/dynamic/public';

// Fallback to localhost:8000 if PUBLIC_API_URL is not set
// We use dynamic env to support runtime configuration if needed
export const API_BASE = env.PUBLIC_API_URL || 'http://localhost:8000';
