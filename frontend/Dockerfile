# Build Stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* bun.lockb* ./

# Install dependencies
# If bun.lockb exists, we might need bun, but for simplicity/compatibility we can try npm 
# or just install bun. Let's install dependencies using npm related tools if lockfile is package-lock
# If user uses bun, they probably have bun.lockb. 
# Let's use a robust approach: install global bun if needed or just use npm if package-lock exists.
# Given the user environment, let's stick to standard Node for build to ensure compatibility with adapter-node.
RUN corepack enable && corepack prepare pnpm@latest --activate
# Or just use npm. 
RUN npm install

# Copy source
COPY . .

# Build
RUN npm run build
# Prune dev dependencies
RUN npm prune --production

# Run Stage
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/build build/
COPY --from=builder /app/node_modules node_modules/
COPY package.json .

EXPOSE 3000

ENV NODE_ENV=production
CMD [ "node", "build" ]
