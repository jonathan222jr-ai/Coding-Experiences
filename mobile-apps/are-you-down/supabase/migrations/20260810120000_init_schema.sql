-- Are You Down? — core schema
-- Campus-scoped, time-limited hangout invites ("drops").
--
-- Privacy note: this app intentionally stores NO location data of any kind.
-- Do not add lat/lng, geohash, or coarse-location columns to any table here.

-- `extensions` already exists on a hosted Supabase project; creating it here
-- keeps the migration runnable against a plain Postgres too.
create schema if not exists extensions;
create extension if not exists pgcrypto with schema extensions;

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

create type public.drop_category as enum ('food', 'errand', 'study', 'workout', 'hangout');
create type public.drop_status   as enum ('open', 'closed', 'expired');
create type public.response_type as enum ('down', 'pass');
create type public.report_target as enum ('drop', 'message', 'user');

-- ---------------------------------------------------------------------------
-- schools
-- ---------------------------------------------------------------------------

create table public.schools (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  email_domain text not null unique,
  created_at   timestamptz not null default now()
);

comment on table public.schools is
  'Allowlist of campuses. A signup email domain must match one of these rows.';

-- ---------------------------------------------------------------------------
-- profiles
-- ---------------------------------------------------------------------------

create table public.profiles (
  id           uuid primary key references auth.users (id) on delete cascade,
  school_id    uuid not null references public.schools (id) on delete restrict,
  display_name text not null check (char_length(display_name) between 1 and 40),
  avatar_url   text,
  created_at   timestamptz not null default now()
);

create index profiles_school_id_idx on public.profiles (school_id);

-- ---------------------------------------------------------------------------
-- drops
-- ---------------------------------------------------------------------------

create table public.drops (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles (id) on delete cascade,
  school_id  uuid not null references public.schools (id) on delete restrict,
  body       text not null check (char_length(body) between 1 and 140),
  category   public.drop_category not null,
  expires_at timestamptz not null,
  status     public.drop_status not null default 'open',
  created_at timestamptz not null default now()
);

-- Primary feed access path: campus + status + expiry window.
create index drops_feed_idx on public.drops (school_id, status, expires_at);
-- Keyset pagination tiebreaker: (created_at desc, id desc).
create index drops_keyset_idx on public.drops (created_at desc, id desc);
create index drops_user_id_idx on public.drops (user_id);

-- ---------------------------------------------------------------------------
-- responses
-- ---------------------------------------------------------------------------

create table public.responses (
  id         uuid primary key default gen_random_uuid(),
  drop_id    uuid not null references public.drops (id) on delete cascade,
  user_id    uuid not null references public.profiles (id) on delete cascade,
  type       public.response_type not null,
  created_at timestamptz not null default now(),
  unique (drop_id, user_id)
);

-- One response per user per drop, enforced above; this index serves the
-- "have I already responded?" lookup in the feed query.
create index responses_user_drop_idx on public.responses (user_id, drop_id);

comment on table public.responses is
  'Private to the responding user. A pass is never revealed to the drop author.';

-- ---------------------------------------------------------------------------
-- threads / thread_users / messages
-- ---------------------------------------------------------------------------

create table public.threads (
  id         uuid primary key default gen_random_uuid(),
  drop_id    uuid not null unique references public.drops (id) on delete cascade,
  created_at timestamptz not null default now()
);

create table public.thread_users (
  id        uuid primary key default gen_random_uuid(),
  thread_id uuid not null references public.threads (id) on delete cascade,
  user_id   uuid not null references public.profiles (id) on delete cascade,
  joined_at timestamptz not null default now(),
  unique (thread_id, user_id)
);

create index thread_users_user_id_idx on public.thread_users (user_id);

create table public.messages (
  id         uuid primary key default gen_random_uuid(),
  thread_id  uuid not null references public.threads (id) on delete cascade,
  user_id    uuid not null references public.profiles (id) on delete cascade,
  body       text not null check (char_length(body) between 1 and 1000),
  created_at timestamptz not null default now()
);

create index messages_thread_created_idx on public.messages (thread_id, created_at desc);

-- ---------------------------------------------------------------------------
-- blocks / reports
-- ---------------------------------------------------------------------------

create table public.blocks (
  id         uuid primary key default gen_random_uuid(),
  blocker_id uuid not null references public.profiles (id) on delete cascade,
  blocked_id uuid not null references public.profiles (id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (blocker_id, blocked_id),
  check (blocker_id <> blocked_id)
);

create index blocks_blocked_id_idx on public.blocks (blocked_id);

create table public.reports (
  id          uuid primary key default gen_random_uuid(),
  reporter_id uuid not null references public.profiles (id) on delete cascade,
  target_type public.report_target not null,
  target_id   uuid not null,
  reason      text not null check (char_length(reason) between 1 and 500),
  created_at  timestamptz not null default now()
);

create index reports_created_at_idx on public.reports (created_at desc);

-- ---------------------------------------------------------------------------
-- push tokens (used by the single notification in the MVP)
-- ---------------------------------------------------------------------------

create table public.push_tokens (
  user_id    uuid not null references public.profiles (id) on delete cascade,
  token      text not null,
  updated_at timestamptz not null default now(),
  primary key (user_id, token)
);
