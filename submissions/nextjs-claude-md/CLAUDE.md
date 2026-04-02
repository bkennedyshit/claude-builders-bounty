# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated rules for this codebase. Every rule has a reason.
> Read this before touching anything. No clarifying questions needed.

---

## Stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | Next.js App Router | 15.x | Server Components = less client JS |
| Database | better-sqlite3 (local) / Turso (prod) | latest | Synchronous API = no async hell in migrations |
| Auth | next-auth v5 | 5.x | App Router native, no client-side token juggling |
| Styling | Tailwind CSS | 3.x | No CSS files. Ever. |
| ORM | None (raw SQL) | — | SQL is readable; ORMs hide intent |
| Validation | zod | 3.x | Schema-first, colocated with types |
| Payments | Stripe | latest | Standard. Use webhooks, not polling. |

---

## Folder Structure

```
app/
  (auth)/           # Auth routes — grouped, no layout inheritance
    login/
    register/
  (dashboard)/      # Protected routes — layout.tsx handles auth check
    dashboard/
    settings/
    billing/
  api/
    webhooks/       # Stripe, etc. — raw Request, no middleware auth
    [...route]/     # All other API routes
  layout.tsx        # Root layout — fonts, providers, analytics
  page.tsx          # Landing page only

components/
  ui/               # Dumb components — no data fetching, no side effects
  forms/            # Client components with useFormState/useFormStatus
  layouts/          # Page-level wrappers (Sidebar, Header, etc.)

lib/
  db.ts             # Single DB connection export — never import better-sqlite3 directly
  auth.ts           # next-auth config — handlers, session shape, callbacks
  stripe.ts         # Stripe client — singleton
  validations/      # Zod schemas — one file per domain (user.ts, billing.ts)
  actions/          # Server Actions — one file per domain

db/
  schema.sql        # Source of truth for schema — human-readable
  migrations/       # Numbered migration files: 001_init.sql, 002_add_teams.sql
  seed.ts           # Dev seed data only

types/
  index.ts          # Shared TypeScript types — inferred from zod schemas when possible
```

**Rule:** If a file is getting long, split by domain — not by type.

---

## Database Rules

### Connection
```ts
// lib/db.ts — THE ONLY PLACE to import better-sqlite3
import Database from 'better-sqlite3'

const db = new Database(process.env.DATABASE_PATH ?? './dev.db', {
  verbose: process.env.NODE_ENV === 'development' ? console.log : undefined,
})

// Enable WAL mode always — faster reads, safe concurrent writes
db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')

export default db
```

### Migrations
- One `.sql` file per migration in `db/migrations/`
- Numbered: `001_init.sql`, `002_add_stripe_customer.sql`
- **Never edit an existing migration.** Always add a new one.
- Run migrations on app startup in `lib/db.ts` — not in a separate CLI

```ts
// Auto-run migrations on startup
import { readdirSync, readFileSync } from 'fs'
import path from 'path'

const migrationsDir = path.join(process.cwd(), 'db/migrations')
const files = readdirSync(migrationsDir).sort()

db.exec(`CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY, ran_at TEXT)`)

for (const file of files) {
  const exists = db.prepare('SELECT 1 FROM _migrations WHERE name = ?').get(file)
  if (!exists) {
    const sql = readFileSync(path.join(migrationsDir, file), 'utf8')
    db.exec(sql)
    db.prepare('INSERT INTO _migrations VALUES (?, ?)').run(file, new Date().toISOString())
  }
}
```

### Query Patterns
```ts
// ✅ Named params always — positional params are a bug waiting to happen
db.prepare('SELECT * FROM users WHERE id = @id').get({ id })

// ✅ Transactions for multi-step writes
const transfer = db.transaction((from: string, to: string, amount: number) => {
  db.prepare('UPDATE accounts SET balance = balance - @amount WHERE id = @id').run({ amount, id: from })
  db.prepare('UPDATE accounts SET balance = balance + @amount WHERE id = @id').run({ amount, id: to })
})

// ❌ Never — string interpolation in SQL
db.prepare(`SELECT * FROM users WHERE id = ${id}`) // SQL injection, instant reject
```

---

## Server Actions

All mutations go through Server Actions in `lib/actions/`. Never mutate from API routes if a Server Action can do it.

```ts
// lib/actions/user.ts
'use server'
import { z } from 'zod'
import db from '@/lib/db'
import { auth } from '@/lib/auth'

const UpdateProfileSchema = z.object({
  name: z.string().min(1).max(100),
  bio: z.string().max(500).optional(),
})

export async function updateProfile(formData: FormData) {
  const session = await auth()
  if (!session?.user?.id) return { error: 'Unauthorized' }

  const parsed = UpdateProfileSchema.safeParse({
    name: formData.get('name'),
    bio: formData.get('bio'),
  })
  if (!parsed.success) return { error: parsed.error.flatten() }

  db.prepare('UPDATE users SET name = @name, bio = @bio WHERE id = @id')
    .run({ ...parsed.data, id: session.user.id })

  return { success: true }
}
```

**Rules:**
- Always validate with zod before touching the DB
- Always check session — never trust client-sent user IDs
- Return `{ error }` or `{ success }` — never throw from Server Actions

---

## Component Patterns

### Server vs Client split

```
Server Component (default):          Client Component (opt-in):
- Data fetching                       - useFormState / useFormStatus
- DB queries (via lib/db.ts)          - useState / useEffect
- Auth checks                         - Event handlers
- Layout / static UI                  - Browser APIs
```

```ts
// ✅ Server Component — fetch at render time, no useEffect
export default async function DashboardPage() {
  const session = await auth()
  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(session.user.id)
  return <Profile user={user} />
}

// ✅ Client Component — only when interactivity needed
'use client'
export function ProfileForm({ action }: { action: typeof updateProfile }) {
  const [state, formAction] = useFormState(action, null)
  return <form action={formAction}>...</form>
}
```

---

## Dev Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run build        # Production build — run before every deploy
npm run lint         # ESLint — must pass before PR
npm run typecheck    # tsc --noEmit — must pass before PR
npm run db:migrate   # Runs on startup automatically, but can force here
npm run db:seed      # Seed dev data (never run in prod)
npm run db:studio    # Opens SQLite browser (uses DB_PATH from .env)
```

---

## What We Don't Do (and Why)

| ❌ Don't | ✅ Do instead | Why |
|---|---|---|
| `useEffect` for data fetching | Server Components | Eliminates loading states and waterfalls |
| Prisma or Drizzle | Raw SQL | SQL intent stays visible; migrations stay explicit |
| `any` TypeScript | Zod-inferred types | Runtime validation = type safety at boundaries |
| API routes for mutations | Server Actions | One round trip, no CSRF tokens needed |
| Multiple DB connections | `lib/db.ts` singleton | WAL mode breaks with multiple connections |
| `.env` in git | `.env.example` only | Obviously |
| `console.log` in prod | Structured logging or nothing | Noise in prod logs is a debugging trap |
| Client-side auth checks | Middleware + Server Component | Easy to bypass client-side checks |
| Inline SQL in components | `lib/actions/` or `lib/db.ts` | SQL belongs in one layer |

---

## Environment Variables

```bash
# .env.local (never commit)
DATABASE_PATH=./dev.db              # Local SQLite path
TURSO_DATABASE_URL=libsql://...     # Prod Turso URL
TURSO_AUTH_TOKEN=...                # Prod Turso token
NEXTAUTH_SECRET=...                 # 32+ char random string
NEXTAUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## Auth Conventions

- Session check in every protected Server Component: `const session = await auth(); if (!session) redirect('/login')`
- Dashboard layout handles redirect once — individual pages trust the layout
- Never store sensitive data in the session JWT — fetch from DB using session.user.id
- Webhook routes (`/api/webhooks/stripe`) skip auth — verify Stripe signature instead

---

## Stripe Integration

```ts
// lib/stripe.ts
import Stripe from 'stripe'
export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2024-06-20' })

// Webhook handler — always verify signature
// app/api/webhooks/stripe/route.ts
export async function POST(req: Request) {
  const body = await req.text()
  const sig = req.headers.get('stripe-signature')!
  const event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  // handle event.type
}
```

**Rules:**
- Update DB from webhooks only — not from client-side success redirects
- Idempotent handlers — Stripe retries, your handler must be safe to call twice
