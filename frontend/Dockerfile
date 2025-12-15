# Build Stage
FROM oven/bun:latest AS builder

WORKDIR /app

# Copy package files
COPY package.json bun.lockb* ./

# Install dependencies
# We use bun install to respect the lockfile
RUN bun install

# Copy source
COPY . .

# Build
RUN bun run build

# Run Stage
FROM oven/bun:latest

WORKDIR /app

# Copy built assets from builder
COPY --from=builder /app/build build/
COPY --from=builder /app/package.json .
# We need production dependencies for the server (adapter-node output usually relies on them)
COPY --from=builder /app/node_modules node_modules/

EXPOSE 3000

ENV NODE_ENV=production
# adapter-node creates a build/index.js entry point
CMD [ "bun", "run", "build/index.js" ]
