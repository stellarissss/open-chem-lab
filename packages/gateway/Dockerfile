# gateway 多阶段构建（仓库根为 build context）
FROM node:22-alpine AS deps
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.28.2 --activate
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml tsconfig.base.json ./
COPY packages/protocol/package.json packages/protocol/
COPY packages/gateway/package.json packages/gateway/
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.28.2 --activate
COPY --from=deps /app ./
COPY schemas schemas
COPY packages/protocol packages/protocol
COPY packages/gateway packages/gateway
RUN pnpm --filter @st/protocol build && pnpm --filter @st/gateway build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production
RUN corepack enable && corepack prepare pnpm@10.28.2 --activate
COPY --from=build /app/pnpm-workspace.yaml /app/package.json /app/pnpm-lock.yaml ./
COPY --from=build /app/packages/protocol ./packages/protocol
COPY --from=build /app/packages/gateway ./packages/gateway
# node_modules 来自 deps 阶段（已含运行时依赖）；devDeps 保留，按需可用 pnpm deploy 裁剪。
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages/gateway/node_modules ./packages/gateway/node_modules
COPY --from=deps /app/packages/protocol/node_modules ./packages/protocol/node_modules
USER node
ENV PORT=3001 HOST=0.0.0.0
EXPOSE 3001
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:'+process.env.PORT+'/api/v1/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "packages/gateway/dist/index.js"]
