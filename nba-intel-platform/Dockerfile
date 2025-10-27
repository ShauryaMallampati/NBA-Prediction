# NBA Intelligence Platform - Frontend (Next.js)

# Multi-stage build
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* pnpm-lock.yaml* ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build Next.js app
RUN npm run build

# Stage 2: Runtime
FROM node:18-alpine

WORKDIR /app

# Install only production dependencies
COPY package.json package-lock.json* pnpm-lock.yaml* ./

RUN npm ci --only=production --legacy-peer-deps

# Copy built app from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.mjs ./

# Set environment variables
ENV NODE_ENV=production \
    NEXT_PUBLIC_BACKEND_URL=http://api:8000

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Start Next.js
CMD ["npm", "start"]
