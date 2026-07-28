FROM node:22-slim AS builder

WORKDIR /web

COPY web-next/package.json web-next/package-lock.json ./
RUN npm ci

COPY web-next/ .

ARG NEXT_PUBLIC_PIT_API_URL
ENV NEXT_PUBLIC_PIT_API_URL=$NEXT_PUBLIC_PIT_API_URL

RUN --mount=type=secret,id=climarket_api_key \
    sh -c 'if [ -f /run/secrets/climarket_api_key ]; then export CLIMARKET_API_KEY="$(cat /run/secrets/climarket_api_key)"; fi; npm run build'

FROM node:22-slim

WORKDIR /web

RUN groupadd -r web && useradd -r -g web -d /web web

COPY --from=builder /web/.next ./.next
COPY --from=builder /web/public ./public
COPY --from=builder /web/package.json /web/package-lock.json ./
COPY --from=builder /web/node_modules ./node_modules

RUN chown -R web:web /web
USER web

ENV NODE_ENV=production
ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "fetch('http://localhost:8080/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["npm", "run", "start"]
