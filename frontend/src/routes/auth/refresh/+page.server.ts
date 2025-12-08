// Auth Refresh - Redirect to backend login for new token
// Upstox token daily expire ஆகும், இந்த route புதிய token வாங்க use ஆகும்

import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
    // Backend login endpoint-க்கு redirect
    // இது Upstox OAuth page-க்கு redirect பண்ணும்
    throw redirect(302, 'http://localhost:8000/api/v1/auth/login');
};
