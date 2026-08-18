-- Make categories legible: give each group a colour, and let the feed be
-- filtered down to one group.
--
-- Two things were true before this migration: 35 categories rendered as 35
-- identical grey pills, and there was no way to ask the feed for one kind of
-- thing. Both are fixed here rather than in the client, for the same reason
-- label and emoji live in the database — adding a group should be an INSERT,
-- and filtering is the feed's job, not the list view's.

-- ---------------------------------------------------------------------------
-- Group colour
--
-- The colour belongs next to the label for exactly the reason the label is not
-- in `src/theme`: a new group otherwise needs an app release before it can
-- render. Constrained to a six-digit hex triple so the client can concatenate
-- an alpha channel onto it without parsing.
-- ---------------------------------------------------------------------------

alter table public.category_groups
  add column color text not null default '#9AA0AE'
  check (color ~ '^#[0-9A-Fa-f]{6}$');

update public.category_groups set color = v.color
from (values
  ('food',    '#FF8A4C'),  -- orange
  ('move',    '#3DDC84'),  -- green
  ('chill',   '#8B7BFF'),  -- violet
  ('study',   '#4CC2FF'),  -- blue
  ('out',     '#FF5B9E'),  -- pink
  ('errands', '#F2C94C')   -- amber
) as v (slug, color)
where public.category_groups.slug = v.slug;

-- ---------------------------------------------------------------------------
-- Feed filtering by group.
--
-- Adding a parameter means a new signature, and two overloads that both accept
-- zero arguments are ambiguous — so the old one is dropped rather than
-- replaced. `p_group` goes last so every existing positional call still
-- resolves.
-- ---------------------------------------------------------------------------

drop function if exists public.get_feed(int, timestamptz, uuid);

create function public.get_feed(
  p_limit              int         default 20,
  p_before_created_at  timestamptz default null,
  p_before_id          uuid        default null,
  p_group              text        default null
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
    -- An unknown group name filters everything out rather than being ignored:
    -- silently returning the unfiltered feed would look like the filter chip
    -- simply doesn't work.
    and (
      p_group is null
      or exists (
        select 1 from public.categories c
        where c.slug = d.category and c.group_slug = p_group
      )
    )
    and (
      p_before_created_at is null
      or (d.created_at, d.id) < (p_before_created_at, p_before_id)
    )
  order by d.created_at desc, d.id desc
  limit least(greatest(coalesce(p_limit, 20), 1), 50);
$$;

revoke execute on function public.get_feed(int, timestamptz, uuid, text) from public, anon;
grant  execute on function public.get_feed(int, timestamptz, uuid, text) to authenticated;
