// Prisma Client Singleton for SvelteKit Server-Side
// Auth Flow க்கு credentials table access பண்ண இந்த file use ஆகும்

import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
    prisma: PrismaClient | undefined;
};

// Singleton pattern - HMR-ல multiple connections avoid பண்ண
export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
    globalForPrisma.prisma = prisma;
}
