-- Drop expiry.
--
-- expires_at is the source of truth — the feed query and the response trigger
-- both compare against now() and never trust `status` alone. This job exists so
-- that stale rows stop matching the (school_id, status, expires_at) index and
-- so the author's own list shows the right state.

create or replace function public.expire_drops()
returns int
language plpgsql
security definer
set search_path = public
as $$
declare
  v_count int;
begin
  update public.drops
  set status = 'expired'
  where status = 'open'
    and expires_at < now();

  get diagnostics v_count = row_count;
  return v_count;
end;
$$;

revoke execute on function public.expire_drops() from public, anon, authenticated;

-- pg_cron is available on Supabase (hosted and local CLI). Guard the whole
-- block so a plain `psql` run against a vanilla Postgres still applies the
-- migration — you would just have to call expire_drops() yourself.
do $$
begin
  create extension if not exists pg_cron;

  perform cron.schedule(
    'expire-drops',
    '* * * * *',
    $job$ select public.expire_drops(); $job$
  );
exception
  when others then
    raise warning 'pg_cron unavailable (%), skipping expire-drops schedule. Call public.expire_drops() manually.', sqlerrm;
end;
$$;
