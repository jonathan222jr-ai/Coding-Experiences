-- Categories: enum -> lookup table.
--
-- `drop_category` started as a Postgres enum, which is cheap to read but
-- expensive to grow: ALTER TYPE ... ADD VALUE cannot be used in the same
-- transaction that adds it, and the label and emoji lived in the app bundle, so
-- every new category needed a migration *and* an App Store release.
--
-- As a table, adding "swim" is one INSERT. The five original slugs are kept
-- verbatim so existing rows migrate without a rewrite.

create table public.category_groups (
  slug       text primary key,
  label      text not null,
  sort_order int  not null default 0
);

create table public.categories (
  slug       text primary key,
  label      text not null,
  emoji      text not null,
  group_slug text not null references public.category_groups (slug) on delete restrict,
  sort_order int  not null default 0,
  -- Retiring a category hides it from the picker without orphaning the drops
  -- that already used it.
  active     boolean not null default true
);

create index categories_group_idx on public.categories (group_slug, sort_order);

-- ---------------------------------------------------------------------------
-- Groups
-- ---------------------------------------------------------------------------

insert into public.category_groups (slug, label, sort_order) values
  ('food',    'Food',    1),
  ('move',    'Move',    2),
  ('chill',   'Chill',   3),
  ('study',   'Study',   4),
  ('out',     'Out',     5),
  ('errands', 'Errands', 6);

-- ---------------------------------------------------------------------------
-- Categories
--
-- food / workout / study / hangout / errand keep their original slugs — those
-- are the values already sitting in public.drops.
-- ---------------------------------------------------------------------------

insert into public.categories (slug, label, emoji, group_slug, sort_order) values
  -- Food
  ('food',          'Food',          '🍜', 'food', 1),
  ('coffee',        'Coffee',        '☕', 'food', 2),
  ('boba',          'Boba',          '🧋', 'food', 3),
  ('dining_hall',   'Dining hall',   '🍽️', 'food', 4),
  ('late_night',    'Late night',    '🌮', 'food', 5),

  -- Move
  ('workout',       'Gym',           '🏋️', 'move', 1),
  ('run',           'Run',           '🏃', 'move', 2),
  ('swim',          'Swim',          '🏊', 'move', 3),
  ('basketball',    'Hoops',         '🏀', 'move', 4),
  ('soccer',        'Soccer',        '⚽', 'move', 5),
  ('climbing',      'Climbing',      '🧗', 'move', 6),
  ('bike',          'Bike',          '🚲', 'move', 7),

  -- Chill
  ('games',         'Video games',   '🎮', 'chill', 1),
  ('movie',         'Movie',         '🎬', 'chill', 2),
  ('anime',         'Anime',         '🍥', 'chill', 3),
  ('tv',            'TV show',       '📺', 'chill', 4),
  ('music',         'Music',         '🎧', 'chill', 5),
  ('board_games',   'Board games',   '🎲', 'chill', 6),

  -- Study
  ('study',         'Study',         '📚', 'study', 1),
  ('group_project', 'Group project', '🧠', 'study', 2),
  ('exam_cram',     'Exam cram',     '😰', 'study', 3),
  ('library',       'Library',       '🤫', 'study', 4),

  -- Out
  ('hangout',       'Hangout',       '🌇', 'out', 1),
  ('walk',          'Walk',          '🚶', 'out', 2),
  ('hike',          'Hike',          '🥾', 'out', 3),
  ('park',          'Park',          '🌳', 'out', 4),
  ('beach',         'Beach',         '🏖️', 'out', 5),
  ('party',         'Party',         '🎉', 'out', 6),
  ('karaoke',       'Karaoke',       '🎤', 'out', 7),
  ('campus_event',  'Campus event',  '🎟️', 'out', 8),

  -- Errands
  ('errand',        'Errand',        '🛒', 'errands', 1),
  ('target_run',    'Target run',    '🎯', 'errands', 2),
  ('groceries',     'Groceries',     '🥕', 'errands', 3),
  ('laundry',       'Laundry',       '🧺', 'errands', 4),
  ('ride',          'Need a ride',   '🚗', 'errands', 5);

-- ---------------------------------------------------------------------------
-- Swap the column.
--
-- The read functions have to go first: their RETURNS TABLE signatures name the
-- enum type, so the type cannot be dropped while they exist.
-- ---------------------------------------------------------------------------

drop function if exists public.get_feed(int, timestamptz, uuid);
drop function if exists public.get_threads();

alter table public.drops add column category_slug text;

update public.drops set category_slug = category::text;

alter table public.drops alter column category_slug set not null;

alter table public.drops
  add constraint drops_category_fkey
  foreign key (category_slug) references public.categories (slug) on delete restrict;

alter table public.drops drop column category;
alter table public.drops rename column category_slug to category;

drop type public.drop_category;

-- ---------------------------------------------------------------------------
-- Read functions, rebuilt against text slugs.
-- ---------------------------------------------------------------------------

create or replace function public.get_feed(
  p_limit              int         default 20,
  p_before_created_at  timestamptz default null,
  p_before_id          uuid        default null
)
returns table (
  id           uuid,
  body         text,
  category     text,
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

create or replace function public.get_threads()
returns table (
  thread_id            uuid,
  drop_id              uuid,
  drop_body            text,
  drop_category        text,
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

revoke execute on function public.get_feed(int, timestamptz, uuid) from public, anon;
revoke execute on function public.get_threads() from public, anon;
grant execute on function public.get_feed(int, timestamptz, uuid) to authenticated;
grant execute on function public.get_threads() to authenticated;

-- ---------------------------------------------------------------------------
-- Access. Categories are a public menu — the auth screen doesn't need them,
-- but the picker does, and there is nothing personal in here.
-- ---------------------------------------------------------------------------

alter table public.categories       enable row level security;
alter table public.category_groups  enable row level security;

create policy categories_select on public.categories
  for select to anon, authenticated
  using (true);

create policy category_groups_select on public.category_groups
  for select to anon, authenticated
  using (true);

grant select on public.categories      to anon, authenticated;
grant select on public.category_groups to anon, authenticated;
