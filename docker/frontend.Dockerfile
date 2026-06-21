# Dev image for the front-end Vite dev server (hot-reload).
FROM node:22-slim

WORKDIR /app/front-end

# Install deps first so the layer caches when only source changes.
COPY front-end/package.json front-end/package-lock.json ./
RUN npm ci

# Source is bind-mounted at runtime; this COPY is a fallback for standalone use.
COPY front-end/ ./

EXPOSE 5173
CMD ["npm", "run", "dev"]
