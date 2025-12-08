// Auth Logout - Clear session and redirect to home
// Frontend-ல session clear பண்ணி home page-க்கு redirect பண்ணும்

import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
    // TODO: Add session clearing logic if cookies/stores are used
    // For now, just redirect home
    throw redirect(302, '/');
};
