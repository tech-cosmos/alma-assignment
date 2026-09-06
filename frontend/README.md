# Alma web (Track C)

Next.js 15 App Router frontend for the lead-intake service. Talks to the FastAPI API described in `docs/PLAN.md` section 5.

## Run

```bash
cp .env.example .env.local   # optional; defaults point at http://localhost:8000
npm install
npm run dev                  # http://localhost:3000
```

No backend yet? Set `NEXT_PUBLIC_API_MOCK=true` in `.env.local` to run against an in-memory mock of the API (`lib/api/mock.ts`). Mock login is `attorney@example.com` / `password123`.

## Pages

| Route | Auth | What |
|---|---|---|
| `/` | public | Lead form: first name, last name, email, resume (pdf/doc/docx, 5 MB). Multipart POST to `/api/v1/leads`. |
| `/login` | public | Attorney sign-in. POST `/api/v1/auth/login`; the API sets the httpOnly cookie. |
| `/leads` | cookie | All leads, state filter (`?state=PENDING|REACHED_OUT`), resume link, "Mark reached out" (PATCH `/api/v1/leads/{id}/state`). |

`middleware.ts` redirects `/leads*` to `/login?next=…` when the auth cookie (`AUTH_COOKIE_NAME`, default `access_token`) is absent.

## API client

`lib/api/schema.d.ts` is generated from `openapi.json` with openapi-typescript; `lib/api/client.ts` wraps it with openapi-fetch. `lib/api/index.ts` exposes small typed helpers (`createLead`, `listLeads`, `markReachedOut`, `login`, `logout`) that normalise FastAPI error bodies into `{ status, message, fields }`.

- `npm run openapi:gen` — regenerate types from the checked-in `openapi.json` (hand-written from the plan for now).
- `npm run openapi:pull` — fetch `$NEXT_PUBLIC_API_URL/openapi.json` from a running backend, overwrite `openapi.json`, and regenerate.

## Checks

```bash
npm run typecheck && npm run lint && npm run build
```

## Docker

```bash
docker build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 -t alma-web .
docker run --rm -p 3000:3000 alma-web
```
