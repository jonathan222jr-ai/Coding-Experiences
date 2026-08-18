# Are you down?

A campus-scoped app for spontaneous hangouts. You post a short, time-limited
invite — *"Are you down to go to Target rn?"* — and other students at your
school either tap **I'm down** or **Pass**. Everyone who's down lands in one
group thread with you. The post expires on a timer.

A pass is permanent, silent, and never shown to anyone — not the author, not
other students. That's enforced in the database, not the client.

**Stack:** Expo (managed) + React Native + TypeScript, Supabase for Postgres /
auth / realtime / row-level security, Expo Push for the one notification this
app sends.

---

## What's worth reading

The interesting part of this app is that **the privacy rules are database
rules.** The client is not trusted with any of them — you could delete the app
and drive the API with `curl`, and every guarantee below still holds.

| To see… | Read |
|---|---|
| Every access rule, as an RLS policy | [`…_rls.sql`](supabase/migrations/20260810120100_rls.sql) |
| Thread creation, the six-person cap, the feed query | [`…_functions.sql`](supabase/migrations/20260810120200_functions.sql) |
| Those rules asserted as behaviour — 89 checks | [`supabase/tests/assert.sql`](supabase/tests/assert.sql) |
| AI report triage that ranks but never decides | [`moderate-report`](supabase/functions/moderate-report/index.ts) |
| A proxy that keeps a vendor API key off the client | [`gif-search`](supabase/functions/gif-search/index.ts) |

Three decisions worth calling out:

- **A pass is unreadable by everyone, including the drop's author.**
  `responses` has a SELECT policy of `user_id = auth.uid()` and no UPDATE or
  DELETE policy at all. Privacy here *is* the product — it's what makes saying
  no safe — so it lives in the schema, not in a component that a later refactor
  could quietly undo.
- **The moderation model ranks the queue and decides nothing.** Auto-acting on
  a classification turns a misclassification into silent censorship, and turns
  coordinated false reporting into a working griefing tool on a campus where
  everyone can see everyone. A human works every report.
- **No location data exists anywhere.** No lat/lng, no geohash, no coarse
  location, no permission request for any of it. A drop is a sentence and a
  timer.

---

## Setup

### 1. Install

```bash
npm install
```

### 2. Start the database

Requires Docker Desktop to be running.

```bash
npx supabase start
```

This applies everything in `supabase/migrations/` and then loads
`supabase/seed.sql`. It prints an **API URL** and an **anon key** when it
finishes — you need both in the next step.

To wipe and reapply after changing a migration:

```bash
npx supabase db reset
```

### 3. Configure the app

```bash
cp .env.example .env
```

Paste the anon key from `supabase start` into `EXPO_PUBLIC_SUPABASE_ANON_KEY`.
The default URL (`http://127.0.0.1:54321`) is already correct for the local
stack.

> On a physical device, `127.0.0.1` points at the phone, not your Mac. Use your
> machine's LAN IP instead — e.g. `http://192.168.1.42:54321`.

### 4. Run

```bash
npx expo start
```

### Useful local URLs

| What | Where |
| --- | --- |
| Studio (browse tables, run SQL) | http://127.0.0.1:54323 |
| Inbucket (catches magic-link emails) | http://127.0.0.1:54324 |
| API | http://127.0.0.1:54321 |

Magic links never leave your machine in local development — they show up in
Inbucket.

---

## Signing in

Enter a school email, get a link. There is no password, no username, no profile
setup step.

The screen accepts either half of the email: tap the link, or type the six-digit
code. The code path exists because deep links back into Expo Go are unreliable —
if the link opens the wrong thing, the code always works.

Locally the email never leaves your machine. Open Inbucket at
http://127.0.0.1:54324 and read it there.

Only domains present in the `schools` table are accepted. The auth screen checks
first so it can tell you *why* an address was refused, but the actual gate is
the `handle_new_user()` trigger, which aborts the signup transaction for an
unknown domain no matter how the request arrives.

> **Testing on a physical device.** Expo Go serves your app from a LAN address,
> so the magic link redirects to something like
> `exp://192.168.1.42:8081/--/auth-callback`. Add that exact URL to
> `additional_redirect_urls` in `supabase/config.toml` and restart the stack, or
> GoTrue will quietly rewrite the link to `site_url` and the tap will go
> nowhere. The six-digit code works regardless.

---

## Seed data

Two campuses, twelve students, fifteen drops.

| Campus | Domain |
| --- | --- |
| UC Merced | `ucmerced.edu` |
| San José State | `sjsu.edu` |

Signing in as `jonathan@ucmerced.edu` gives you a UC Merced feed; anything
outside those two domains is rejected at signup by a database trigger.

The seed deliberately includes edge cases: two expired drops, one closed drop,
a pre-seeded thread with messages, a block pair, and a report — so the feed
filters and the admin views have something real to show.

All seeded users have the password `password123`, which only matters if you
temporarily switch the auth screen to password sign-in for debugging.

---

## Layout

```
src/
  api/          every Supabase call lives here — never inline in a component
  components/   small, typed, presentational
  screens/      one file per screen
  hooks/
  lib/          supabase client, env
  theme/
  types/        database types
supabase/
  migrations/   schema, RLS, functions, triggers, cron, push
  functions/    Edge Functions (AI report triage)
  seed.sql
  tests/        throwaway-Postgres assertions (npm run test:sql)
```

Components don't talk to Supabase. They call `src/api/`, which is the only
place that imports the client.

---

## How the rules are enforced

Every rule below is a database rule. The client can be patched, rebuilt, or
replaced with `curl` and none of it changes:

- **Campus scoping** — you can only read drops whose `school_id` matches your
  own profile's. RLS policy on `drops`.
- **Private responses** — `responses` has a SELECT policy of
  `user_id = auth.uid()` and no UPDATE or DELETE policy at all. The author of a
  drop cannot see who passed on it. Nobody can.
- **One answer per drop** — `UNIQUE (drop_id, user_id)`, plus no UPDATE policy,
  so an answer is final.
- **Thread privacy** — reading `messages` requires membership in
  `thread_users`, checked through a `SECURITY DEFINER` helper so the policy
  doesn't recurse.
- **Thread creation** — the first `down` response creates the thread and seats
  the author, via a `BEFORE INSERT` trigger on `responses`. Concurrent first
  responses are serialised with `SELECT ... FOR UPDATE` on the drop.
- **Six-person cap** — same trigger. Author plus five.
- **Closed / expired drops** — the trigger rejects a `down` against either.
- **Blocking is bidirectional** — the feed hides drops in both directions, and
  the response trigger refuses the join server-side too.
- **Signup gating** — a trigger on `auth.users` looks up the email domain in
  `schools` and raises if there's no match, which aborts the signup.
- **Table privileges** — RLS narrows access but never grants it, so each table
  is also `GRANT`ed only the verbs its policies permit. There is no UPDATE or
  DELETE on `responses`, no INSERT on `threads` or `thread_users` (the trigger
  owns those), and no SELECT on `reports`. Both layers have to agree, so a
  missing policy fails closed twice.

`get_feed()` and `get_threads()` are `SECURITY DEFINER` because they need to
consult rows RLS deliberately hides from the caller — specifically, blocks where
*you* are the blocked party, which you must not be able to read directly. Both
restate every access predicate explicitly against `auth.uid()` rather than
leaning on the caller's policies.

### Location

This app stores no location data. There is no lat/lng, no geohash, no coarse
location, and no permission request for any of it. A drop is a sentence and a
timer. Please keep it that way.

### Moderation

Reports are write-only from the client — there's an INSERT policy and no SELECT
policy, so nobody can enumerate them. Read them with the service role:

```sql
select * from admin.reports_detail;
select * from admin.most_reported_users;
```

The `admin` schema isn't exposed through the API, so those views are reachable
only from the SQL editor or a service-role connection.

---

## Testing the database

```bash
npm run test:sql
```

Applies every migration and the seed to a throwaway Postgres container, then
asserts the behaviour the app depends on — feed filtering, keyset pagination,
each RLS policy, the thread cap, campus gating, the expiry sweep, and the admin
views. 89 checks, a few seconds to run.

It is deliberately *not* the Supabase stack. `supabase/tests/bootstrap.sql`
stubs the handful of things Supabase provides from outside our migrations — the
`auth` schema, `auth.uid()`, the `anon` / `authenticated` roles, the realtime
publication — which is enough to exercise everything we ship without booting
GoTrue, Studio and the rest. `auth.uid()` reads a session variable there, so a
test can act as any seeded user and see exactly what RLS lets them see.

pg_cron isn't available in that container, which conveniently also exercises the
expiry migration's fallback path.

Run it after any change under `supabase/migrations/`.

### Against the real thing

```bash
npm run test:e2e
```

Needs `npx supabase start` running. Signs in as seeded users over the real auth
endpoint and drives PostgREST with their JWTs — the exact path the app takes.
21 checks: feed contents, campus scoping, private responses, thread creation,
the duplicate and cross-campus refusals, and that an anonymous caller is
refused on `drops` but allowed on `schools`.

It mutates data, so reset first:

```bash
npx supabase db reset && npm run test:e2e
```

Keep both suites. The offline one is fast and runs anywhere; this one catches
what stubs cannot — grants, PostgREST's view of the schema, and GoTrue.

---

## Safety

Report and block are reachable from every drop card (the `⋯` on the card), from
inside every thread (tap the member count), and from any individual message
(long-press it). Reports are typed as `drop`, `message`, or `user` accordingly.

Blocking is bidirectional and silent. Neither of you appears in the other's
feed, the response trigger refuses joins in either direction, and the blocked
person is never told — the `blocks` SELECT policy only matches rows where you
are the blocker, so nobody can discover who blocked them.

The blocked list, with unblock, lives on the Profile tab.

Reports are write-only from the app — there's no SELECT grant at all, so a
read is refused before RLS is even consulted. Read them with the service role:

```sql
select * from admin.moderation_queue;   -- unresolved, worst first
select * from admin.reports_detail;     -- everything
select * from admin.most_reported_users;
```

Two abuse limits sit on `reports`: `UNIQUE (reporter_id, target_type,
target_id)` so one person can't report the same thing repeatedly to inflate its
rank, and ten reports per reporter per hour.

### AI triage

Each new report is handed to the `moderate-report` Edge Function, which asks
Claude how likely it is to be a real violation and writes a verdict,
confidence, categories, and a one-line reason back onto the row.

**The model ranks the queue. It does not decide anything.** Nothing in this app
hides, deletes, or blocks based on `ai_verdict` — a human works every report.
That's deliberate: auto-acting on a classification turns a misclassification
into silent censorship, and turns coordinated false reporting into a working
griefing tool on a campus where everyone can see everyone.

Untriaged reports sort *with* `unclear`, never last — an unreviewed report is
not a low-priority one.

Turning it on (optional — the queue works without it):

```bash
npx supabase functions deploy moderate-report
npx supabase secrets set ANTHROPIC_API_KEY=sk-ant-... MODERATION_SHARED_SECRET=$(openssl rand -hex 32)
```

Then point the trigger at it, using the same shared secret:

```sql
select vault.create_secret('https://<project-ref>.supabase.co/functions/v1/moderate-report',
                           'moderation_function_url');
select vault.create_secret('<the same MODERATION_SHARED_SECRET>',
                           'moderation_shared_secret');
```

Without those two secrets the trigger is a no-op and reports stay `pending` for
a human — exactly as they did before triage existed. The same is true if the
API call fails: the verdict is written as `error` and the report keeps its place
in the queue. A failed model call must never lose a report.

---

## Categories

Every drop has exactly one category, and the categories live in the database —
`category_groups` (6) and `categories` (35) — rather than in the bundle. Adding
"swim" is one INSERT: no migration, no App Store release. That only pays off if
the client never hardcodes the list, which is why `useCategories()` is the only
way a screen learns a label, an emoji, or a colour.

The taxonomy is two levels, and the UI says so in both directions:

| Level | Where it shows up |
| --- | --- |
| **Group** — Food, Move, Chill, Study, Out, Errands | The filter bar over the feed; the tabs in the drop composer; the headings in the interest picker |
| **Category** — Boba, Hoops, Exam cram, … | The chip on every card, thread row, and thread header |

`category_groups.color` is the reason a card is scannable. Thirty-five
categories in one grey pill meant the chip carried an emoji and nothing else;
tinting every chip by its group makes the kind of thing legible before you read
the words. The colour is a column and not a constant in `src/theme` for exactly
the reason the label is: a seventh group should not need an app release. A
CHECK pins it to a six-digit hex triple, so the client appends an alpha channel
by concatenation rather than parsing.

**Filtering happens in `get_feed()`, via `p_group`.** Not in the list view.
A client-side filter would shrink each page rather than the result set, so
"nothing in Food right now" and "you've reached the end" would be
indistinguishable — and paging would fetch drops only to throw them away. An
unrecognised group returns nothing rather than being ignored, because silently
falling back to the unfiltered feed looks exactly like a broken chip.

The composer's group tabs are deliberately *not* the same control as the
category chips. When both were pills that filled with the accent colour,
"Out" selected looked identical to "Hangout" selected — one control shape for
two different meanings, which is most of why the two levels weren't obvious.

---

## GIFs

GIFs are available **in thread messages only** — not in drops. A drop is a
sentence and a timer, seen campus-wide; a meme picker there trades the thing
that makes posting frictionless for performative posts competing for attention.
A thread is at most six people who already opted in, which is a far smaller
blast radius for the single largest moderation surface in the app.

The app never talks to Tenor directly. `supabase/functions/gif-search` proxies
every query, which keeps the API key off the client — an `EXPO_PUBLIC_` key ships
inside the bundle and can be lifted out of it — and, more importantly, enforces
`contentfilter=high` server-side. If the client built the query, the strictest
safety setting would be one edited request away from being off for everyone.

A message can be text, a GIF, or both, but never neither.

**`gif_url` is pinned to Tenor's CDN by a CHECK constraint.** This is the
load-bearing line. Without it the column is free text that every thread member's
device fetches on sight: an arbitrary-image embed, a tracking pixel harvesting
IPs, or a link to something that never passed the safe-search filter. Five
assertions cover it, including a `media.tenor.com.evil.example` lookalike and a
mismatched preview/full pair.

Turning it on locally — put the key in `.env` (it is **not** `EXPO_PUBLIC_`, so
it never reaches the app) and restart the stack, because `[edge_runtime.secrets]`
in `supabase/config.toml` reads it at start:

```bash
echo 'TENOR_API_KEY=your-key' >> .env
npx supabase stop && npx supabase start
```

Against a hosted project instead:

```bash
npx supabase functions deploy gif-search
npx supabase secrets set TENOR_API_KEY=...
```

Get a key from [Google Cloud](https://developers.google.com/tenor/guides/quickstart).

Without a key the function answers 503 and the picker says GIF search isn't set
up yet; messages still send. That is a configured state, not a broken one — the
broken one is a **404**, which means the function isn't being served at all.
`npm run test:e2e` tells the two apart, because "the GIF button does nothing"
looked the same from the outside either way.

Check it by hand:

```bash
curl -s -i "http://127.0.0.1:54321/functions/v1/gif-search?q=boba" -H "Authorization: Bearer $ANON_KEY"
```

---

## Notifications

Exactly one push: the drop's author is told when somebody joins their thread.
Nothing else notifies. In particular there is no "someone passed on your drop",
which is the entire reason passes are private.

It is sent by a trigger on `thread_users`, which collects the author's Expo push
tokens and POSTs them to Expo in one request via `pg_net`. The whole function is
wrapped in an exception handler: **a failed notification must never roll back
the join that caused it.** Being in the thread is what matters; the push is a
courtesy. There's a test for exactly that.

### Turning it on

Push needs two things that a fresh clone doesn't have:

1. **An EAS project id.** Run `eas init`, then put the id in `app.json` under
   `extra.eas.projectId`. Without it, registration logs a warning and skips —
   the app works fine, it just never notifies.
2. **A development build.** Expo Go on Android has not supported remote push
   since SDK 53. Use `eas build --profile development` or a local dev client.

Simulators can't be issued a push token at all, so registration no-ops there.

`pg_net` is available on hosted Supabase. If it's missing the migration warns
instead of failing, and joins keep working without notifications.

---

## Expiry

`expires_at` is the source of truth. The feed query and the response trigger
both compare against `now()` and never trust `status` on its own, so a drop is
effectively dead the moment it expires regardless of when the job last ran.

A `pg_cron` job sweeps every minute to set `status = 'expired'`, which keeps
stale rows out of the feed index and makes the author's view correct. If
`pg_cron` isn't available, the migration logs a warning instead of failing and
you can call `select public.expire_drops();` yourself.
