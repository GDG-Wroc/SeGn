FROM node:24-alpine AS build

WORKDIR /workspace

COPY package.json package-lock.json nx.json tsconfig.base.json ./
COPY apps/my-hackathon-app ./apps/my-hackathon-app

RUN npm ci
RUN npx nx build my-hackathon-app --configuration=production

FROM nginx:1.29-alpine

ENV PORT=8080
ENV API_BASE_URL=""

COPY apps/my-hackathon-app/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY apps/my-hackathon-app/docker-entrypoint.d/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
COPY --from=build /workspace/dist/apps/my-hackathon-app/browser /usr/share/nginx/html

RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh

EXPOSE 8080
