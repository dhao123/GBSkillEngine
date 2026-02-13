# GBSkillEngine Frontend Dockerfile
# 支持开发和生产两种模式

# ==================== Base Stage ====================
FROM node:20-alpine AS base

WORKDIR /app

# Copy package files
COPY package*.json ./

# ==================== Development Stage ====================
FROM base AS development

RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ==================== Build Stage ====================
FROM base AS builder

RUN npm ci

COPY . .

# Build for production
RUN npm run build

# ==================== Production Stage ====================
FROM nginx:alpine AS production

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config for SPA routing
RUN echo 'server { \
    listen 5173; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /assets { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]

# ==================== Default Stage ====================
FROM development
