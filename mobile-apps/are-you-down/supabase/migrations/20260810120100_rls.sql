-- Row-level security.
--
-- Every rule the product depends on is enforced here, not in the client.
-- The client is treated as hostile; screens only ever get a nicer error message.

-- ---------------------------------------------------------------------------
-- Helpers
--
-- These are SECURITY DEFINER so that a policy on table X can consult table Y
-- without recursing back through Y's own policies (the classic
-- "infinite recursion detected in policy" trap with thread membership).
-- ---------------------------------------------------------------------------

create or replace function public.current_school_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select school_id from public.profiles where id = auth.uid();
$$;

create or replace function public.is_thread_member(p_thread_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.thread_users tu
    where tu.thread_id = p_thread_id
      and tu.user_id = auth.uid()
  );
$$;

revoke execute on function public.current_school_id() from public, anon;
revoke execute on function public.is_thread_member(uuid) from public, anon;
grant execute on function public.current_school_id() to authenticated;
grant execute on function public.is_thread_member(uuid) to authenticated;

-- ---------------------------------------------------------------------------
-- Enable RLS everywhere. Default-deny: a table with RLS on and no matching
-- policy returns zero rows and rejects every write.
-- ---------------------------------------------------------------------------

alter table public.schools      enable row level security;
alter table public.profiles     enable row level security;
alter table public.drops        enable row level security;
alter table public.responses    enable row level security;
alter table public.threads      enable row level security;
alter table public.thread_users enable row level security;
alter table public.messages     enable row level security;
alter table public.blocks       enable row level security;
alter table public.reports      enable row level security;
alter table public.push_tokens  enable row level security;

-- ---------------------------------------------------------------------------
-- Table privileges.
--
-- RLS narrows what a role can see, but it never grants anything: a role with no
-- GRANT is refused before a policy is ever consulted. So both layers have to
-- agree, and each table below is granted only the verbs its policies actually
-- allow. A missing policy then fails closed twice over.
--
-- Note what is absent: no UPDATE or DELETE on responses (an answer is final),
-- no INSERT on threads or thread_users (only the response trigger writes
-- those), and no SELECT on reports (write-only from the client).
-- ---------------------------------------------------------------------------

grant usage on schema public to anon, authenticated;

grant select                         on public.schools      to anon, authenticated;
grant select, update                 on public.profiles     to authenticated;
grant select, insert, update, delete on public.drops        to authenticated;
grant select, insert                 on public.responses    to authenticated;
grant select                         on public.threads      to authenticated;
grant select                         on public.thread_users to authenticated;
grant select, insert                 on public.messages     to authenticated;
grant select, insert, delete         on public.blocks       to authenticated;
grant insert                         on public.reports      to authenticated;
grant select, insert, update, delete on public.push_tokens  to authenticated;

-- ---------------------------------------------------------------------------
-- schools — public read (the auth screen must check a domain before the user
-- has any session at all). Contains no personal data.
-- ---------------------------------------------------------------------------

create policy schools_select on public.schools
  for select to anon, authenticated
  using (true);

-- ---------------------------------------------------------------------------
-- profiles — you can see yourself and everyone else on your campus.
-- Rows are created by the on-signup trigger, never by the client, so there is
-- deliberately no INSERT policy.
-- ---------------------------------------------------------------------------

create policy profiles_select_same_school on public.profiles
  for select to authenticated
  using (id = auth.uid() or school_id = public.current_school_id());

create policy profiles_update_own on public.profiles
  for update to authenticated
  using (id = auth.uid())
  with check (id = auth.uid());

-- ---------------------------------------------------------------------------
-- drops — campus-scoped read; author-only write.
-- ---------------------------------------------------------------------------

create policy drops_select_same_school on public.drops
  for select to authenticated
  using (school_id = public.current_school_id());

create policy drops_insert_own on public.drops
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and school_id = public.current_school_id()
    and expires_at > now()
  );

create policy drops_update_own on public.drops
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid() and school_id = public.current_school_id());

create policy drops_delete_own on public.drops
  for delete to authenticated
  using (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- responses — strictly private to the responder.
--
-- The drop's author cannot read these. Neither can anyone else. There is no
-- UPDATE or DELETE policy, so a response is permanent: combined with the
-- UNIQUE (drop_id, user_id) constraint that gives exactly one irrevocable
-- answer per drop per user.
-- ---------------------------------------------------------------------------

create policy responses_select_own on public.responses
  for select to authenticated
  using (user_id = auth.uid());

create policy responses_insert_own on public.responses
  for insert to authenticated
  with check (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- threads / thread_users — members only.
-- Rows are written by the response trigger (SECURITY DEFINER), so no INSERT
-- policy is granted to users.
-- ---------------------------------------------------------------------------

create policy threads_select_member on public.threads
  for select to authenticated
  using (public.is_thread_member(id));

create policy thread_users_select_member on public.thread_users
  for select to authenticated
  using (public.is_thread_member(thread_id));

-- ---------------------------------------------------------------------------
-- messages — read and write restricted to thread members.
-- ---------------------------------------------------------------------------

create policy messages_select_member on public.messages
  for select to authenticated
  using (public.is_thread_member(thread_id));

create policy messages_insert_member on public.messages
  for insert to authenticated
  with check (user_id = auth.uid() and public.is_thread_member(thread_id));

-- ---------------------------------------------------------------------------
-- blocks — you manage your own block list and can only see your own.
-- Critically, you cannot read rows where you are the blocked party: that would
-- tell you who blocked you.
-- ---------------------------------------------------------------------------

create policy blocks_select_own on public.blocks
  for select to authenticated
  using (blocker_id = auth.uid());

create policy blocks_insert_own on public.blocks
  for insert to authenticated
  with check (blocker_id = auth.uid());

create policy blocks_delete_own on public.blocks
  for delete to authenticated
  using (blocker_id = auth.uid());

-- ---------------------------------------------------------------------------
-- reports — write-only from the client. No SELECT policy at all: reporters
-- cannot re-read their reports and nobody can enumerate them. Moderators read
-- them through the admin schema with the service role.
-- ---------------------------------------------------------------------------

create policy reports_insert_own on public.reports
  for insert to authenticated
  with check (reporter_id = auth.uid());

-- ---------------------------------------------------------------------------
-- push_tokens — own rows only.
-- ---------------------------------------------------------------------------

create policy push_tokens_select_own on public.push_tokens
  for select to authenticated
  using (user_id = auth.uid());

create policy push_tokens_insert_own on public.push_tokens
  for insert to authenticated
  with check (user_id = auth.uid());

create policy push_tokens_update_own on public.push_tokens
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy push_tokens_delete_own on public.push_tokens
  for delete to authenticated
  using (user_id = auth.uid());
