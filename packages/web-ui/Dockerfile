# web-ui 构建 + nginx 托管（仓库根为 build context）
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.28.2 --activate
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml tsconfig.base.json ./
COPY packages/protocol/package.json packages/protocol/
COPY packages/web-ui/package.json packages/web-ui/
RUN pnpm install --frozen-lockfile
COPY schemas schemas
COPY packages/protocol packages/protocol
COPY packages/web-ui packages/web-ui
RUN pnpm --filter @st/protocol build && pnpm --filter @st/web-ui build

FROM nginx:1.27-alpine AS run
COPY packages/web-ui/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/packages/web-ui/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1
