-- Minimal stand-in for the parts of a Supabase project that live outside our
-- migrations, so the migrations can be applied to a plain Postgres and tested.
-- This file is a test harness only; it is not part of the app.

\set ON_ERROR_STOP on

-- Roles are cluster-wide, so tolerate them surviving a previous run.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then
    create role service_role nologin bypassrls;
  end if;
end $$;

grant usage on schema public to anon, authenticated, service_role;

-- Deliberately NOT granting blanket default privileges on tables.
--
-- An earlier version of this file did, and it hid a real bug: the migrations
-- were missing their GRANT statements entirely, so every table worked here and
-- returned "permission denied" against a real Supabase project. The harness has
-- to be at least as strict as production, so table privileges must come from
-- the migrations themselves.
alter default privileges in schema public
  grant execute on functions to anon, authenticated, service_role;

create schema if not exists extensions;

-- ---------------------------------------------------------------------------
-- auth schema
-- ---------------------------------------------------------------------------

create schema auth;

create table auth.users (
  instance_id            uuid,
  id                     uuid primary key,
  aud                    varchar(255),
  role                   varchar(255),
  email                  varchar(255) unique,
  encrypted_password     varchar(255),
  email_confirmed_at     timestamptz,
  raw_app_meta_data      jsonb,
  raw_user_meta_data     jsonb,
  created_at             timestamptz,
  updated_at             timestamptz,
  confirmation_token     varchar(255),
  recovery_token         varchar(255),
  email_change_token_new varchar(255),
  email_change           varchar(255)
);

create table auth.identities (
  id              uuid primary key,
  user_id         uuid not null references auth.users (id) on delete cascade,
  provider_id     text not null,
  identity_data   jsonb not null,
  provider        text not null,
  last_sign_in_at timestamptz,
  created_at      timestamptz,
  updated_at      timestamptz,
  unique (provider_id, provider)
);

-- The real auth.uid() reads the request's JWT claims. For testing, read a GUC
-- we can set per-statement.
create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select nullif(current_setting('app.current_user_id', true), '')::uuid;
$$;

grant usage on schema auth to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;

-- Realtime publication, so the migration's ALTER PUBLICATION finds a target.
create publication supabase_realtime;
