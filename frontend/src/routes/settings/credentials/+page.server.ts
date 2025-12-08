// Load existing credentials from Prisma DB
// Server-side ல credentials fetch பண்ணி page-க்கு pass பண்ணும்

import type { PageServerLoad } from './$types';
import { prisma } from '$lib/server/prisma';

export const load: PageServerLoad = async () => {
    try {
        const credentials = await prisma.credential.findFirst({
            where: { id: 1 },
            select: {
                apiKey: true,
                redirectUri: true,
                accessToken: true,
                // apiSecret should NOT be sent to client for security
            }
        });

        return {
            credentials: credentials ? {
                apiKey: credentials.apiKey,
                apiSecret: '', // Never expose secret to client
                redirectUri: credentials.redirectUri,
                hasToken: !!credentials.accessToken
            } : null
        };
    } catch (error) {
        console.error('Failed to load credentials:', error);
        return { credentials: null };
    }
};
