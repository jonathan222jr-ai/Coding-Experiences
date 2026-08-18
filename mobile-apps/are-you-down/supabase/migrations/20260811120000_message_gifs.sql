-- GIFs in thread messages.
--
-- Threads only — not drops. A drop is a sentence and a timer, and it is
-- campus-wide; adding a meme picker there trades the thing that makes posting
-- frictionless for performative posts competing for attention. A thread is at
-- most six people who already opted in, which is a far smaller blast radius for
-- the single largest moderation surface in the app.

-- ---------------------------------------------------------------------------
-- A message is now text, a GIF, or both — but never neither.
-- ---------------------------------------------------------------------------

alter table public.messages drop constraint if exists messages_body_check;
alter table public.messages alter column body drop not null;

alter table public.messages
  add column gif_id          text,
  add column gif_url         text,
  add column gif_preview_url text,
  add column gif_width       int,
  add column gif_height      int,
  -- Tenor ships a description per GIF. Carrying it means the bubble can be
  -- announced to a screen reader as something other than "image".
  add column gif_alt         text;

alter table public.messages
  add constraint messages_body_length
    check (body is null or char_length(body) between 1 and 1000),

  add constraint messages_has_content
    check (body is not null or gif_id is not null),

  -- Half a GIF renders as a broken bubble; keep the pieces together.
  add constraint messages_gif_complete
    check (
      (gif_id is null and gif_url is null and gif_preview_url is null)
      or (gif_id is not null and gif_url is not null and gif_preview_url is not null)
    ),

  -- The single most important line in this migration.
  --
  -- Without it, `gif_url` is a free-text field that every thread member's
  -- device will fetch on sight: an arbitrary-image embed, a tracking pixel that
  -- harvests IPs, or a link to content that never passed the safe-search
  -- filter. Pinning it to Tenor's CDN means a message can only ever point at
  -- something the search proxy actually returned.
  add constraint messages_gif_host
    check (
      gif_url is null
      or (
        gif_url ~ '^https://media[0-9]*\.tenor\.com/'
        and gif_preview_url ~ '^https://media[0-9]*\.tenor\.com/'
      )
    );

comment on column public.messages.gif_url is
  'Tenor CDN only, enforced by the messages_gif_host constraint. Never widen this to arbitrary URLs.';

-- ---------------------------------------------------------------------------
-- Thread previews
--
-- A GIF-only message has no body, which would render the threads list as a
-- blank preview line.
-- ---------------------------------------------------------------------------

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
    coalesce(m.body, case when m.gif_id is not null then 'GIF' end),
    m.created_at,
    mp.display_name
  from public.threads t
  join public.thread_users me on me.thread_id = t.id and me.user_id = auth.uid()
  join public.drops d on d.id = t.drop_id
  left join lateral (
    -- Qualified for the same reason as get_feed: `thread_id` is also the name
    -- of this function's first output column.
    select last.body, last.gif_id, last.created_at, last.user_id
    from public.messages last
    where last.thread_id = t.id
    order by last.created_at desc
    limit 1
  ) m on true
  left join public.profiles mp on mp.id = m.user_id
  order by coalesce(m.created_at, t.created_at) desc;
$$;

revoke execute on function public.get_threads() from public, anon;
grant execute on function public.get_threads() to authenticated;
