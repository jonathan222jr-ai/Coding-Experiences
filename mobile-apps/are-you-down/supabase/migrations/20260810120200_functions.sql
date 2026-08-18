-- Server-side logic: signup gating, response handling, and read-time queries.

-- ---------------------------------------------------------------------------
-- 1. Signup gating
--
-- A profile is never created by the client. When GoTrue inserts into
-- auth.users we derive the campus from the email domain; an unrecognised
-- domain raises, which aborts the signup transaction entirely.
-- ---------------------------------------------------------------------------

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_domain    text;
  v_school_id uuid;
  v_name      text;
begin
  v_domain := lower(split_part(new.email, '@', 2));

  select id into v_school_id
  from public.schools
  where email_domain = v_domain;

  if v_school_id is null then
    raise exception 'The email domain % is not a supported campus.', v_domain
      using errcode = '22023';
  end if;

  -- Prefer a name the client passed in signup metadata, otherwise humanise the
  -- local part of the address ("jane.doe" -> "Jane Doe").
  v_name := coalesce(
    nullif(trim(new.raw_user_meta_data ->> 'display_name'), ''),
    initcap(replace(split_part(new.email, '@', 1), '.', ' '))
  );

  insert into public.profiles (id, school_id, display_name)
  values (new.id, v_school_id, left(v_name, 40));

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------------------
-- 2. Response handling
--
-- Runs BEFORE INSERT on responses, so every rule below holds regardless of
-- what the client sends:
--   * a 'pass' is recorded and nothing else happens — it is invisible forever
--   * a 'down' requires the drop to still be open and unexpired
--   * the first 'down' creates the thread and seats the author
--   * the thread is capped at 6 members total (author + 5)
--   * a block in either direction rejects the join
-- ---------------------------------------------------------------------------

create or replace function public.handle_response()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_drop      public.drops;
  v_thread_id uuid;
  v_members   int;
begin
  -- FOR UPDATE serialises concurrent first-'down' responses so that exactly
  -- one of them creates the thread.
  select * into v_drop from public.drops where id = new.drop_id for update;

  if not found then
    raise exception 'That drop no longer exists.' using errcode = 'P0002';
  end if;

  if new.user_id = v_drop.user_id then
    raise exception 'You cannot respond to your own drop.' using errcode = '42501';
  end if;

  -- RLS on `responses` only checks that you are inserting as yourself, so
  -- without this a crafted request could answer a drop at another campus.
  -- Reading the drop is already impossible cross-campus; answering one has to
  -- be too.
  if v_drop.school_id <> (select p.school_id from public.profiles p where p.id = new.user_id) then
    raise exception 'That drop is not from your campus.' using errcode = '42501';
  end if;

  -- A pass is purely a private feed filter. Stop here: no thread, no
  -- notification, no trace anyone else can observe.
  --
  -- Note this sits above the block check. Passing on a drop from someone you
  -- have since blocked is harmless and invisible, and erroring on it would
  -- only strand a stale feed card that the user is trying to dismiss.
  if new.type = 'pass' then
    return new;
  end if;

  if exists (
    select 1 from public.blocks b
    where (b.blocker_id = new.user_id and b.blocked_id = v_drop.user_id)
       or (b.blocker_id = v_drop.user_id and b.blocked_id = new.user_id)
  ) then
    raise exception 'This drop is not available to you.' using errcode = '42501';
  end if;

  if v_drop.status <> 'open' then
    raise exception 'This drop is closed.' using errcode = 'P0001';
  end if;

  if v_drop.expires_at <= now() then
    raise exception 'This drop has expired.' using errcode = 'P0001';
  end if;

  select id into v_thread_id from public.threads where drop_id = v_drop.id;

  if v_thread_id is null then
    insert into public.threads (drop_id)
    values (v_drop.id)
    returning id into v_thread_id;

    insert into public.thread_users (thread_id, user_id)
    values (v_thread_id, v_drop.user_id);
  end if;

  select count(*) into v_members
  from public.thread_users
  where thread_id = v_thread_id;

  if v_members >= 6 then
    raise exception 'This hangout is full.' using errcode = 'P0001';
  end if;

  insert into public.thread_users (thread_id, user_id)
  values (v_thread_id, new.user_id)
  on conflict (thread_id, user_id) do nothing;

  return new;
end;
$$;

drop trigger if exists responses_before_insert on public.responses;
create trigger responses_before_insert
  before insert on public.responses
  for each row execute function public.handle_response();

-- ---------------------------------------------------------------------------
-- 3. Feed query
--
-- SECURITY DEFINER on purpose: the bidirectional block filter has to consult
-- rows where the caller is the *blocked* party, and RLS deliberately hides
-- those from them. Every other predicate is re-stated here explicitly, so the
-- function is not relying on the caller's policies for correctness.
--
-- Keyset pagination: pass the (created_at, id) of the last row you rendered.
-- ---------------------------------------------------------------------------

create or replace function public.get_feed(
  p_limit              int         default 20,
  p_before_created_at  timestamptz default null,
  p_before_id          uuid        default null
)
returns table (
  id           uuid,
  body         text,
  category     public.drop_category,
  expires_at   timestamptz,
  created_at   timestamptz,
  author_id    uuid,
  display_name text,
  avatar_url   text
)
language sql
stable
security definer
set search_path = public
as $$
  -- Every column reference below is table-qualified on purpose: the RETURNS
  -- TABLE names (id, body, created_at, ...) are in scope inside this body, and
  -- an unqualified reference that matches one is an ambiguity error at runtime.
  select d.id, d.body, d.category, d.expires_at, d.created_at,
         d.user_id, p.display_name, p.avatar_url
  from public.drops d
  join public.profiles p on p.id = d.user_id
  where d.school_id = (select me.school_id from public.profiles me where me.id = auth.uid())
    and d.status = 'open'
    and d.expires_at > now()
    and d.user_id <> auth.uid()
    and not exists (
      select 1 from public.responses r
      where r.drop_id = d.id and r.user_id = auth.uid()
    )
    and not exists (
      select 1 from public.blocks b
      where (b.blocker_id = auth.uid() and b.blocked_id = d.user_id)
         or (b.blocker_id = d.user_id and b.blocked_id = auth.uid())
    )
    and (
      p_before_created_at is null
      or (d.created_at, d.id) < (p_before_created_at, p_before_id)
    )
  order by d.created_at desc, d.id desc
  limit least(greatest(coalesce(p_limit, 20), 1), 50);
$$;

-- ---------------------------------------------------------------------------
-- 4. Threads list, with the most recent message preview.
--
-- SECURITY DEFINER, but the membership predicate is stated explicitly against
-- auth.uid() — a caller only ever sees threads they are seated in.
-- ---------------------------------------------------------------------------

create or replace function public.get_threads()
returns table (
  thread_id            uuid,
  drop_id              uuid,
  drop_body            text,
  drop_category        public.drop_category,
  drop_status          public.drop_status,
  drop_author_id       uuid,
  member_count         int,
  last_message_body    text,
  last_message_at      timestamptz,
  last_message_author  text
)
language sql
stable
security definer
set search_path = public
as $$
  select
    t.id,
    d.id,
    d.body,
    d.category,
    d.status,
    d.user_id,
    (select count(*)::int from public.thread_users tu where tu.thread_id = t.id),
    m.body,
    m.created_at,
    mp.display_name
  from public.threads t
  join public.thread_users me on me.thread_id = t.id and me.user_id = auth.uid()
  join public.drops d on d.id = t.drop_id
  left join lateral (
    -- Qualified for the same reason as get_feed: `thread_id` is also the name
    -- of this function's first output column.
    select last.body, last.created_at, last.user_id
    from public.messages last
    where last.thread_id = t.id
    order by last.created_at desc
    limit 1
  ) m on true
  left join public.profiles mp on mp.id = m.user_id
  order by coalesce(m.created_at, t.created_at) desc;
$$;

-- ---------------------------------------------------------------------------
-- Grants. Nothing here is reachable by anon.
-- ---------------------------------------------------------------------------

revoke execute on function public.get_feed(int, timestamptz, uuid) from public, anon;
revoke execute on function public.get_threads() from public, anon;
grant execute on function public.get_feed(int, timestamptz, uuid) to authenticated;
grant execute on function public.get_threads() to authenticated;

-- ---------------------------------------------------------------------------
-- Realtime: thread chat subscribes to message inserts. RLS still applies to
-- the replicated rows, so non-members receive nothing.
-- ---------------------------------------------------------------------------

do $$
begin
  alter publication supabase_realtime add table public.messages;
exception
  when undefined_object then
    raise warning 'No supabase_realtime publication here; thread chat will not stream.';
  when duplicate_object then
    null;
end;
$$;
