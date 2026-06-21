# Next.js frontend — production build served by `next start`.
# Single-stage on purpose: robust to Next 16's changes (see AGENTS.md) and image
# size doesn't matter for a local-dev convenience container.
FROM node:20-slim

WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Install deps first for layer caching.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_* vars are inlined into the bundle at build time, so the API URL must
# be known here. It has to be reachable from the user's BROWSER (which runs lib/api.ts),
# not from inside the compose network — hence localhost, not the "backend" service name.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

EXPOSE 3000
ENV PORT=3000
CMD ["npm", "run", "start"]
