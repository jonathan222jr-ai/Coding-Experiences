-- GIFs in drops.
--
-- This reverses the decision in 20260811120000_message_gifs.sql, which put GIFs
-- in threads only. That migration's argument still stands and is worth reading
-- before widening this further: a drop is campus-wide, so it is a far larger
-- moderation surface than a thread of at most six people who opted in.
--
-- Two things keep the change narrower than "images in posts":
--
--   1. `body` stays NOT NULL. A drop is still a sentence and a timer; the GIF
--      is an addition to the sentence, never a replacement for it. There is no
--      such thing as a GIF-only drop, so nothing that reads a drop's text —
--      the threads list, the report queue, push notifications — has to grow a
--      null case.
--   2. The Tenor CDN pin is copied verbatim from messages. Everything the app
--      can display still had to come back from the search proxy, which is the
--      only thing enforcing `contentfilter=high`.

alter table public.drops
  add column gif_id          text,
  add column gif_url         text,
  add column gif_preview_url text,
  add column gif_width       int,
  add column gif_height      int,
  -- Tenor ships a description per GIF, so a card can be announced to a screen
  -- reader as something other than "image".
  add column gif_alt         text;

alter table public.drops
  -- Half a GIF renders as a broken card; keep the pieces together.
  add constraint drops_gif_complete
    check (
      (gif_id is null and gif_url is null and gif_preview_url is null)
      or (gif_id is not null and gif_url is not null and gif_preview_url is not null)
    ),

  -- The single most important line in this migration, and more load-bearing
  -- here than it is on messages: a drop is seen by the whole campus, so a
  -- free-text URL would be an arbitrary-image embed or an IP-harvesting
  -- tracking pixel fetched by every student's device at once.
  add constraint drops_gif_host
    check (
      gif_url is null
      or (
        gif_url ~ '^https://media[0-9]*\.tenor\.com/'
        and gif_preview_url ~ '^https://media[0-9]*\.tenor\.com/'
      )
    );

comment on column public.drops.gif_url is
  'Tenor CDN only, enforced by the drops_gif_host constraint. Never widen this to arbitrary URLs.';

-- ---------------------------------------------------------------------------
-- The feed has to carry the GIF.
--
-- Changing the RETURNS TABLE shape means dropping and recreating rather than
-- replacing. `p_group` keeps its position, so nothing that calls this needs to
-- change.
-- ---------------------------------------------------------------------------

drop function if exists public.get_feed(int, timestamptz, uuid, text);

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
  avatar_url   text,
  gif_url      text,
  gif_width    int,
  gif_height   int,
  gif_alt      text
)
language sql
stable
security definer
set search_path = public
as $$
  -- Every column reference below is table-qualified on purpose: the RETURNS
  -- TABLE names (id, body, created_at, ...) are in scope inside this body, and
  -- an unqualified reference that matches one is an ambiguity error at runtime.
  --
  -- gif_preview_url is deliberately not returned: the card shows the full GIF,
  -- and the preview size only exists for the picker's grid.
  select d.id, d.body, d.category, d.expires_at, d.created_at,
         d.user_id, p.display_name, p.avatar_url,
         d.gif_url, d.gif_width, d.gif_height, d.gif_alt
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
